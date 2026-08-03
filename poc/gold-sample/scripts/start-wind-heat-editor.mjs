import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import revideoModule from '@revideo/vite-plugin';
import {createServer} from 'vite';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(scriptDir, '..');
const repositoryRoot = path.resolve(projectRoot, '../..');
const projectFile = path.resolve(
  projectRoot,
  'src/wind-heat-editable-project.tsx',
);
const pluginFile = path.resolve(
  projectRoot,
  'src/editor/wind-heat-editable-plugin.tsx',
);
const validationDir = path.resolve(
  repositoryRoot,
  'production-library/validation/revideo-editability/wind-heat',
);
const currentStateFile = path.resolve(validationDir, 'current-candidate.json');
const candidateAssetsDir = path.resolve(validationDir, 'assets');
const exportRoot = path.resolve(validationDir, 'exports');
const port = Number(process.env.REVIDEO_EDITOR_PORT ?? 9000);
const revideo = revideoModule.default ?? revideoModule;

fs.mkdirSync(validationDir, {recursive: true});
fs.mkdirSync(candidateAssetsDir, {recursive: true});
fs.mkdirSync(exportRoot, {recursive: true});

function readState() {
  if (!fs.existsSync(currentStateFile)) return {patches: {}};
  return JSON.parse(fs.readFileSync(currentStateFile, 'utf8'));
}

function persistInlineAssets(patches) {
  const normalized = structuredClone(patches);
  for (const patch of Object.values(normalized)) {
    if (typeof patch.src !== 'string' || !patch.src.startsWith('data:image/')) {
      continue;
    }
    const match = patch.src.match(/^data:image\/(png|jpeg|webp);base64,(.+)$/);
    if (!match) continue;
    const extension = match[1] === 'jpeg' ? 'jpg' : match[1];
    const contents = Buffer.from(match[2], 'base64');
    const hash = crypto.createHash('sha256').update(contents).digest('hex');
    const filename = `${hash}.${extension}`;
    const target = path.resolve(candidateAssetsDir, filename);
    if (!fs.existsSync(target)) fs.writeFileSync(target, contents);
    patch.src = `/__wind_heat_editor/assets/${filename}`;
  }
  return normalized;
}

function writeJson(target, value) {
  fs.writeFileSync(target, `${JSON.stringify(value, null, 2)}\n`);
}

function persistExportAssets(patches, exportDir) {
  const normalized = structuredClone(patches);
  const assetsDir = path.resolve(exportDir, 'assets');
  fs.mkdirSync(assetsDir, {recursive: true});

  for (const patch of Object.values(normalized)) {
    if (typeof patch.src !== 'string') continue;

    if (patch.src.startsWith('/__wind_heat_editor/assets/')) {
      const filename = path.basename(patch.src);
      const source = path.resolve(candidateAssetsDir, filename);
      const target = path.resolve(assetsDir, filename);
      if (fs.existsSync(source) && !fs.existsSync(target)) {
        fs.copyFileSync(source, target);
      }
      patch.src = `assets/${filename}`;
      continue;
    }

    const match = patch.src.match(
      /^data:image\/(png|jpeg|webp);base64,(.+)$/,
    );
    if (!match) continue;
    const extension = match[1] === 'jpeg' ? 'jpg' : match[1];
    const contents = Buffer.from(match[2], 'base64');
    const hash = crypto.createHash('sha256').update(contents).digest('hex');
    const filename = `${hash}.${extension}`;
    const target = path.resolve(assetsDir, filename);
    if (!fs.existsSync(target)) fs.writeFileSync(target, contents);
    patch.src = `assets/${filename}`;
  }

  return normalized;
}

function updateExportStatus(exportDir, patch) {
  const target = path.resolve(exportDir, 'status.json');
  const current = fs.existsSync(target)
    ? JSON.parse(fs.readFileSync(target, 'utf8'))
    : {};
  writeJson(target, {...current, ...patch});
}

function startExport(format, patches) {
  if (!['video', 'pptx'].includes(format)) {
    throw new Error('Unsupported export format.');
  }

  const now = new Date();
  const timestamp = now
    .toISOString()
    .replace(/[-:]/g, '')
    .replace(/\..+/, 'Z');
  const exportId =
    `${timestamp}-${format}-${crypto.randomBytes(3).toString('hex')}`;
  const exportDir = path.resolve(exportRoot, exportId);
  const snapshotFile = path.resolve(exportDir, 'project.json');
  const outputName =
    format === 'video'
      ? '风热证_当前作品.mp4'
      : '风热证_当前作品_可编辑课件.pptx';
  const script =
    format === 'video'
      ? path.resolve(scriptDir, 'export-wind-heat-video.mjs')
      : path.resolve(scriptDir, 'export-wind-heat-pptx.mjs');

  fs.mkdirSync(exportDir, {recursive: true});
  writeJson(snapshotFile, {
    export_id: exportId,
    project_id: 'health.wind-heat.editable-v2',
    template_id: 'template.health-reference-tech-v1',
    style_pack_id: 'style-pack.reference-medical-tech-v1',
    status: 'project-export',
    format,
    created_at: now.toISOString(),
    patches: persistExportAssets(patches, exportDir),
  });
  updateExportStatus(exportDir, {
    ok: true,
    export_id: exportId,
    format,
    status: 'queued',
    output_name: outputName,
    created_at: now.toISOString(),
  });

  const logFile = path.resolve(exportDir, 'export.log');
  const logFd = fs.openSync(logFile, 'a');
  const child = spawn(process.execPath, [script, snapshotFile], {
    cwd: projectRoot,
    stdio: ['ignore', logFd, logFd],
  });
  fs.closeSync(logFd);
  updateExportStatus(exportDir, {
    status: 'running',
    started_at: new Date().toISOString(),
    pid: child.pid,
  });

  child.on('error', error => {
    updateExportStatus(exportDir, {
      ok: false,
      status: 'failed',
      error: String(error.message ?? error),
      finished_at: new Date().toISOString(),
    });
  });
  child.on('close', code => {
    const outputFile = path.resolve(exportDir, outputName);
    updateExportStatus(exportDir, {
      ok: code === 0 && fs.existsSync(outputFile),
      status:
        code === 0 && fs.existsSync(outputFile) ? 'completed' : 'failed',
      exit_code: code,
      finished_at: new Date().toISOString(),
      ...(code === 0 && fs.existsSync(outputFile)
        ? {
            download_url:
              `/__wind_heat_editor/export/${exportId}/download`,
            size_bytes: fs.statSync(outputFile).size,
          }
        : {
            error: '生成失败，请查看导出记录。',
          }),
    });
  });

  return {
    ok: true,
    export_id: exportId,
    status: 'running',
    status_url: `/__wind_heat_editor/export/${exportId}/status`,
  };
}

function editorPersistencePlugin() {
  return {
    name: 'wind-heat-editor-persistence',
    enforce: 'pre',
    resolveId(id) {
      if (id === 'wind-heat-editable-plugin') return pluginFile;
    },
    configureServer(server) {
      server.middlewares.use((request, response, next) => {
        if (request.url?.startsWith('/__wind_heat_editor/assets/')) {
          const filename = path.basename(request.url);
          const target = path.resolve(candidateAssetsDir, filename);
          if (!fs.existsSync(target)) {
            response.statusCode = 404;
            response.end('Not found');
            return;
          }
          const extension = path.extname(filename);
          response.setHeader(
            'Content-Type',
            extension === '.jpg' ? 'image/jpeg' : `image/${extension.slice(1)}`,
          );
          fs.createReadStream(target).pipe(response);
          return;
        }
        if (request.url === '/__wind_heat_editor/state') {
          response.setHeader('Content-Type', 'application/json');
          response.end(JSON.stringify(readState()));
          return;
        }
        const exportRoute = request.url?.match(
          /^\/__wind_heat_editor\/export\/([A-Za-z0-9-]+)\/(status|download)$/,
        );
        if (exportRoute && request.method === 'GET') {
          const [, exportId, action] = exportRoute;
          const exportDir = path.resolve(exportRoot, exportId);
          const statusFile = path.resolve(exportDir, 'status.json');
          if (
            !exportDir.startsWith(`${exportRoot}${path.sep}`) ||
            !fs.existsSync(statusFile)
          ) {
            response.statusCode = 404;
            response.end('Not found');
            return;
          }
          const status = JSON.parse(fs.readFileSync(statusFile, 'utf8'));
          if (action === 'status') {
            response.setHeader('Content-Type', 'application/json');
            response.end(JSON.stringify(status));
            return;
          }
          const outputFile = path.resolve(exportDir, status.output_name ?? '');
          if (
            status.status !== 'completed' ||
            !fs.existsSync(outputFile)
          ) {
            response.statusCode = 409;
            response.end('Export is not ready');
            return;
          }
          response.setHeader(
            'Content-Type',
            status.format === 'video'
              ? 'video/mp4'
              : 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
          );
          response.setHeader(
            'Content-Disposition',
            `attachment; filename*=UTF-8''${encodeURIComponent(
              status.output_name,
            )}`,
          );
          fs.createReadStream(outputFile).pipe(response);
          return;
        }
        if (
          request.url === '/__wind_heat_editor/export' &&
          request.method === 'POST'
        ) {
          let body = '';
          request.setEncoding('utf8');
          request.on('data', chunk => {
            body += chunk;
            if (body.length > 40 * 1024 * 1024) request.destroy();
          });
          request.on('end', () => {
            try {
              const payload = JSON.parse(body);
              const result = startExport(
                payload.format,
                payload.patches ?? {},
              );
              response.setHeader('Content-Type', 'application/json');
              response.end(JSON.stringify(result));
            } catch (error) {
              response.statusCode = 400;
              response.setHeader('Content-Type', 'application/json');
              response.end(
                JSON.stringify({
                  ok: false,
                  error: String(error.message ?? error),
                }),
              );
            }
          });
          return;
        }
        if (
          request.url !== '/__wind_heat_editor/save' ||
          request.method !== 'POST'
        ) {
          next();
          return;
        }

        let body = '';
        request.setEncoding('utf8');
        request.on('data', chunk => {
          body += chunk;
        });
        request.on('end', () => {
          try {
            const payload = JSON.parse(body);
            const now = new Date();
            const timestamp = now.toISOString().replace(/[-:.]/g, '');
            const version =
              `${timestamp}-${crypto.randomBytes(2).toString('hex')}`;
            const candidate = {
              template_id: 'template.health-reference-tech-v1',
              style_pack_id: 'style-pack.reference-medical-tech-v1',
              status: 'candidate',
              version,
              saved_at: now.toISOString(),
              patches: persistInlineAssets(payload.patches ?? {}),
            };
            const versionFile = path.resolve(
              validationDir,
              `candidate-${version}.json`,
            );
            fs.writeFileSync(
              versionFile,
              `${JSON.stringify(candidate, null, 2)}\n`,
              {flag: 'wx'},
            );
            writeJson(currentStateFile, candidate);
            response.setHeader('Content-Type', 'application/json');
            response.end(JSON.stringify({ok: true, version}));
          } catch (error) {
            response.statusCode = 400;
            response.setHeader('Content-Type', 'application/json');
            response.end(
              JSON.stringify({ok: false, error: String(error.message ?? error)}),
            );
          }
        });
      });
    },
  };
}

const server = await createServer({
  configFile: false,
  root: projectRoot,
  plugins: [
    editorPersistencePlugin(),
    revideo({project: projectFile, buildForEditor: false}),
  ],
  build: {
    minify: false,
    rollupOptions: {output: {entryFileNames: '[name].js'}},
  },
  server: {host: '127.0.0.1', port},
});

await server.listen();
console.log(`Wind-heat editable Revideo project: http://127.0.0.1:${port}`);
