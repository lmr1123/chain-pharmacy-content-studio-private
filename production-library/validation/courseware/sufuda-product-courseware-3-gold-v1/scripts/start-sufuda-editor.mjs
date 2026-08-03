/**
 * 启动速福达课件业务编辑器（复用 wind-heat 插件）。
 * 导出 PPTX 走本目录 export-sufuda-pptx.mjs；导出视频走 gold-sample 渲染链需另开。
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import revideoModule from '@revideo/vite-plugin';
import {createServer} from 'vite';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(scriptDir, '..');
const repoRoot = path.resolve(projectRoot, '../../../..');
const goldSampleRoot = path.resolve(repoRoot, 'poc/gold-sample');
// Bridge project lives inside gold-sample so Vite root + JSX runtime stay stable.
// Real scene source remains under this gold directory (imported relatively).
const projectFile = path.resolve(
  goldSampleRoot,
  'src/sufuda-courseware-editable-project.tsx',
);
const pluginFile = path.resolve(
  goldSampleRoot,
  'src/editor/wind-heat-editable-plugin.tsx',
);
const validationDir = path.resolve(
  repoRoot,
  'production-library/validation/revideo-editability/sufuda',
);
const currentStateFile = path.resolve(validationDir, 'current-candidate.json');
const candidateAssetsDir = path.resolve(validationDir, 'assets');
const exportRoot = path.resolve(validationDir, 'exports');
const port = Number(process.env.REVIDEO_EDITOR_PORT ?? 9010);
const revideo = revideoModule.default ?? revideoModule;

fs.mkdirSync(validationDir, {recursive: true});
fs.mkdirSync(candidateAssetsDir, {recursive: true});
fs.mkdirSync(exportRoot, {recursive: true});

function readState() {
  if (!fs.existsSync(currentStateFile)) return {patches: {}};
  return JSON.parse(fs.readFileSync(currentStateFile, 'utf8'));
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
    const match = patch.src.match(/^data:image\/(png|jpeg|webp);base64,(.+)$/);
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
  const timestamp = now.toISOString().replace(/[-:]/g, '').replace(/\..+/, 'Z');
  const exportId = `${timestamp}-${format}-${crypto.randomBytes(3).toString('hex')}`;
  const exportDir = path.resolve(exportRoot, exportId);
  const snapshotFile = path.resolve(exportDir, 'project.json');
  const outputName =
    format === 'video'
      ? '速福达_当前作品.mp4'
      : '速福达_当前作品_可编辑课件.pptx';

  fs.mkdirSync(exportDir, {recursive: true});
  writeJson(snapshotFile, {
    export_id: exportId,
    project_id: 'courseware.sufuda-product-training-3.gold-v1',
    template_id: 'template.sufuda-product-courseware-3-v1',
    style_pack_id: 'style-pack.sufuda-pearl-silk-orange-v1',
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
  let child;
  if (format === 'pptx') {
    const outFile = path.resolve(exportDir, outputName);
    child = spawn(
      process.execPath,
      [
        path.resolve(scriptDir, 'export-sufuda-pptx.mjs'),
        snapshotFile,
        '--model',
        path.resolve(projectRoot, 'content-model.json'),
        '--assets',
        path.resolve(projectRoot, 'public'),
        '--out',
        outFile,
      ],
      {cwd: projectRoot, stdio: ['ignore', logFd, logFd]},
    );
  } else {
    // Video: render via project render.ts (patches not fully wired in headless yet)
    child = spawn(
      process.execPath,
      [
        path.resolve(goldSampleRoot, 'node_modules/tsx/dist/cli.mjs'),
        path.resolve(projectRoot, 'src/render.ts'),
      ],
      {
        cwd: projectRoot,
        stdio: ['ignore', logFd, logFd],
        env: {...process.env, SUFUDA_EXPORT_DIR: exportDir},
      },
    );
  }
  fs.closeSync(logFd);

  child.on('close', code => {
    const outputFile = path.resolve(exportDir, outputName);
    // Video renderer writes to out/ — copy if present
    if (format === 'video' && code === 0) {
      const rendered = path.resolve(
        projectRoot,
        'out',
        '速福达_商品培训课件3_独立金样_v1.mp4',
      );
      if (fs.existsSync(rendered)) {
        fs.copyFileSync(rendered, outputFile);
      }
    }
    updateExportStatus(exportDir, {
      ok: code === 0 && fs.existsSync(outputFile),
      status:
        code === 0 && fs.existsSync(outputFile) ? 'completed' : 'failed',
      exit_code: code,
      finished_at: new Date().toISOString(),
      ...(code === 0 && fs.existsSync(outputFile)
        ? {
            download_url: `/__wind_heat_editor/export/${exportId}/download`,
            size_bytes: fs.statSync(outputFile).size,
          }
        : {error: '生成失败，请查看导出记录。'}),
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
    name: 'sufuda-editor-persistence',
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
          response.setHeader('Content-Type', 'image/png');
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
          if (!fs.existsSync(statusFile)) {
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
          if (status.status !== 'completed' || !fs.existsSync(outputFile)) {
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
            `attachment; filename*=UTF-8''${encodeURIComponent(status.output_name)}`,
          );
          fs.createReadStream(outputFile).pipe(response);
          return;
        }
        if (request.url === '/__wind_heat_editor/export' && request.method === 'POST') {
          let body = '';
          request.setEncoding('utf8');
          request.on('data', chunk => {
            body += chunk;
          });
          request.on('end', () => {
            try {
              const payload = JSON.parse(body);
              const result = startExport(payload.format, payload.patches ?? {});
              response.setHeader('Content-Type', 'application/json');
              response.end(JSON.stringify(result));
            } catch (error) {
              response.statusCode = 400;
              response.end(JSON.stringify({ok: false, error: String(error.message ?? error)}));
            }
          });
          return;
        }
        if (request.url === '/__wind_heat_editor/save' && request.method === 'POST') {
          let body = '';
          request.setEncoding('utf8');
          request.on('data', chunk => {
            body += chunk;
          });
          request.on('end', () => {
            try {
              const payload = JSON.parse(body);
              const now = new Date();
              const version = `${now.toISOString().replace(/[-:.]/g, '')}-${crypto.randomBytes(2).toString('hex')}`;
              const candidate = {
                template_id: 'template.sufuda-product-courseware-3-v1',
                style_pack_id: 'style-pack.sufuda-pearl-silk-orange-v1',
                status: 'candidate',
                version,
                saved_at: now.toISOString(),
                patches: payload.patches ?? {},
              };
              writeJson(path.resolve(validationDir, `candidate-${version}.json`), candidate);
              writeJson(currentStateFile, candidate);
              response.setHeader('Content-Type', 'application/json');
              response.end(JSON.stringify({ok: true, version}));
            } catch (error) {
              response.statusCode = 400;
              response.end(JSON.stringify({ok: false, error: String(error.message ?? error)}));
            }
          });
          return;
        }
        next();
      });
    },
  };
}

const nm = path.resolve(goldSampleRoot, 'node_modules');

const server = await createServer({
  configFile: false,
  // Editor UI + deps live under gold-sample; project sources stay in this gold dir.
  root: goldSampleRoot,
  publicDir: path.resolve(projectRoot, 'public'),
  plugins: [
    editorPersistencePlugin(),
    revideo({project: projectFile, buildForEditor: false}),
  ],
  build: {
    minify: false,
    rollupOptions: {output: {entryFileNames: '[name].js'}},
  },
  // Project files live outside gold-sample root via @fs. Without this, Vite falls
  // back to classic React.createElement and the scene crashes with "React is not defined".
  esbuild: {
    jsx: 'automatic',
    jsxImportSource: '@revideo/2d/lib',
  },
  // Vite 8+ path (ignored on Vite 4, kept for forward compatibility)
  oxc: {
    jsx: {
      runtime: 'automatic',
      importSource: '@revideo/2d/lib',
    },
  },
  server: {
    host: '127.0.0.1',
    port,
    strictPort: true,
    fs: {
      // node_modules is symlinked from gold-sample; Vite realpath must be allowed
      allow: [goldSampleRoot, projectRoot, nm, repoRoot],
      strict: true,
    },
  },
  resolve: {
    alias: {
      '@revideo/2d': path.resolve(nm, '@revideo/2d'),
      '@revideo/core': path.resolve(nm, '@revideo/core'),
      '@revideo/ui': path.resolve(nm, '@revideo/ui'),
    },
  },
});

// Serve sufuda public assets under /assets even though Vite root is gold-sample
server.middlewares.use((req, res, next) => {
  if (!req.url?.startsWith('/assets/')) return next();
  const file = path.resolve(projectRoot, 'public', req.url.slice(1));
  if (!file.startsWith(path.resolve(projectRoot, 'public') + path.sep)) {
    res.statusCode = 403;
    res.end('Forbidden');
    return;
  }
  if (!fs.existsSync(file) || !fs.statSync(file).isFile()) return next();
  const ext = path.extname(file).toLowerCase();
  const type =
    ext === '.png'
      ? 'image/png'
      : ext === '.jpg' || ext === '.jpeg'
        ? 'image/jpeg'
        : ext === '.wav'
          ? 'audio/wav'
          : ext === '.mp3'
            ? 'audio/mpeg'
            : 'application/octet-stream';
  res.setHeader('Content-Type', type);
  fs.createReadStream(file).pipe(res);
});

await server.listen();
console.log(`Sufuda courseware VIDEO editor: http://127.0.0.1:${port}/`);
console.log(`Project: ${projectFile}`);
console.log(`State dir: ${validationDir}`);
console.log('Right panel: 画面属性 — edit editable:sufuda:* layers, export MP4/PPTX.');
