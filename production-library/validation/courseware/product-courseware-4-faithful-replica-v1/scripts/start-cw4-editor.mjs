/**
 * 启动商品培训课件4业务编辑器（复用 wind-heat editable 插件）。
 * 视频导出：src/render.ts（Revideo）或退回 PIL export-full-film-video.py
 * PPTX：本包禁用。
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawn, spawnSync} from 'node:child_process';
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
  'src/cw4-courseware-editable-project.tsx',
);
const pluginFile = path.resolve(
  goldSampleRoot,
  'src/editor/wind-heat-editable-plugin.tsx',
);
const validationDir = path.resolve(
  repoRoot,
  'production-library/validation/revideo-editability/courseware-4',
);
const currentStateFile = path.resolve(validationDir, 'current-candidate.json');
const candidateAssetsDir = path.resolve(validationDir, 'assets');
const exportRoot = path.resolve(validationDir, 'exports');
const port = Number(process.env.REVIDEO_EDITOR_PORT ?? 9012);
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
      ? '商品培训课件4_当前作品.mp4'
      : '商品培训课件4_当前作品.pptx';

  fs.mkdirSync(exportDir, {recursive: true});
  writeJson(snapshotFile, {
    export_id: exportId,
    project_id: 'product-courseware-4-faithful-replica-v1',
    template_id: 'template.product-courseware-4-faithful-replica-v1',
    style_pack_id: 'style-pack.courseware-training-shared-v1',
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
    fs.closeSync(logFd);
    updateExportStatus(exportDir, {
      ok: false,
      status: 'failed',
      error: 'courseware-4: PPTX disabled; export video only',
      finished_at: new Date().toISOString(),
    });
    return {
      ok: false,
      export_id: exportId,
      status: 'failed',
      error: 'PPTX disabled for courseware-4',
    };
  } else {
    // Video: prefer signed still-film (PIL) for visual fidelity; Revideo optional
    child = spawn(
      'python3',
      [path.resolve(projectRoot, 'scripts/export-full-film-video.py')],
      {
        cwd: projectRoot,
        stdio: ['ignore', logFd, logFd],
        env: {...process.env, CW4_EXPORT_DIR: exportDir},
      },
    );
  }
  fs.closeSync(logFd);

  child.on('close', code => {
    const outputFile = path.resolve(exportDir, outputName);
    // Video renderer writes to out/ — copy if present
    if (format === 'video') {
      const pil = path.resolve(
        projectRoot,
        'out',
        '商品培训课件4_保真复刻_全片_v1.mp4',
      );
      if (fs.existsSync(pil)) {
        fs.copyFileSync(pil, outputFile);
        code = 0;
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
    name: 'cw4-editor-persistence',
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
                template_id: 'template.product-courseware-4-faithful-replica-v1',
                style_pack_id: 'style-pack.courseware-training-shared-v1',
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

        // —— 片段编排工作室（删段 / 改旁白 / TTS / 重建）——
        const segStudio = path.resolve(projectRoot, 'scripts/segment_studio.py');
        // Prefer project venv with mlx-audio + mlx-lm for Qwen3 clone
        const ttsPython = fs.existsSync(
          path.resolve(projectRoot, '.venv-tts/bin/python'),
        )
          ? path.resolve(projectRoot, '.venv-tts/bin/python')
          : 'python3';
        const runSeg = (args, timeoutMs = 600000) => {
          const r = spawnSync(ttsPython, [segStudio, ...args], {
            cwd: projectRoot,
            encoding: 'utf8',
            timeout: timeoutMs,
            maxBuffer: 8 * 1024 * 1024,
            env: {
              ...process.env,
              PYTHONPATH: [
                path.resolve(repoRoot, 'third_party/mlx-audio'),
                process.env.PYTHONPATH || '',
              ]
                .filter(Boolean)
                .join(path.delimiter),
            },
          });
          const out = (r.stdout || '').trim();
          let data;
          try {
            data = out ? JSON.parse(out.split('\n').filter(Boolean).at(-1)) : {};
          } catch {
            data = {ok: r.status === 0, raw: out.slice(-2000)};
          }
          if (r.status !== 0 && data.ok !== true) {
            data.ok = false;
            data.error = data.error || r.stderr?.slice(-1500) || `exit ${r.status}`;
          }
          return data;
        };
        const readJsonBody = () =>
          new Promise((resolve, reject) => {
            let body = '';
            request.setEncoding('utf8');
            request.on('data', c => {
              body += c;
            });
            request.on('end', () => {
              try {
                resolve(body ? JSON.parse(body) : {});
              } catch (e) {
                reject(e);
              }
            });
          });
        const jsonRes = (code, obj) => {
          response.statusCode = code;
          response.setHeader('Content-Type', 'application/json');
          response.end(JSON.stringify(obj));
        };

        if (request.url === '/__cw4_segments/list' && request.method === 'GET') {
          // ensure state exists
          if (
            !fs.existsSync(
              path.resolve(projectRoot, 'out/segment-studio/state.json'),
            )
          ) {
            runSeg(['init']);
          }
          return jsonRes(200, runSeg(['api-list']));
        }
        if (request.url === '/__cw4_segments/hide' && request.method === 'POST') {
          readJsonBody()
            .then(p => jsonRes(200, runSeg(['hide', '--id', String(p.id || '')])))
            .catch(e => jsonRes(400, {ok: false, error: String(e)}));
          return;
        }
        if (request.url === '/__cw4_segments/enable' && request.method === 'POST') {
          readJsonBody()
            .then(p =>
              jsonRes(200, runSeg(['enable', '--id', String(p.id || '')])),
            )
            .catch(e => jsonRes(400, {ok: false, error: String(e)}));
          return;
        }
        if (
          request.url === '/__cw4_segments/set-narration' &&
          request.method === 'POST'
        ) {
          readJsonBody()
            .then(p => {
              const args = [
                'set-narration',
                '--id',
                String(p.id || ''),
                '--text',
                String(p.text || ''),
              ];
              if (p.keep_reference) args.push('--keep-reference');
              jsonRes(200, runSeg(args));
            })
            .catch(e => jsonRes(400, {ok: false, error: String(e)}));
          return;
        }
        if (
          request.url === '/__cw4_segments/regen-tts' &&
          request.method === 'POST'
        ) {
          readJsonBody()
            .then(p => {
              const args = ['regen-tts', '--id', String(p.id || '')];
              if (p.text) args.push('--text', String(p.text));
              if (p.voice) args.push('--voice', String(p.voice));
              // auto | clone | edge | say — default auto (Qwen3 clone first)
              args.push('--backend', String(p.backend || 'auto'));
              // clone may load model + generate: allow up to 15 min
              jsonRes(200, runSeg(args, 900000));
            })
            .catch(e => jsonRes(400, {ok: false, error: String(e)}));
          return;
        }
        if (request.url === '/__cw4_segments/rebuild' && request.method === 'POST') {
          readJsonBody()
            .then(p => {
              const args = ['rebuild'];
              if (p.film !== false) args.push('--film');
              jsonRes(200, runSeg(args, 900000));
            })
            .catch(e => jsonRes(400, {ok: false, error: String(e)}));
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

// Serve courseware-4 public assets (/assets, /stills, narration) even though Vite root is gold-sample
server.middlewares.use((req, res, next) => {
  if (!req.url?.match(/^\/(assets|stills|stills-editor-bg|narration\.mp3)/)) return next();
  const rel = req.url.split('?')[0].replace(/^\//, '');
  const file = path.resolve(projectRoot, 'public', rel);
  const pubRoot = path.resolve(projectRoot, 'public');
  if (!file.startsWith(pubRoot + path.sep) && file !== pubRoot) {
    // allow realpath through symlink
    const real = fs.existsSync(file) ? fs.realpathSync(file) : file;
    // ok if under projectRoot
    if (!real.startsWith(projectRoot + path.sep)) {
      res.statusCode = 403;
      res.end('Forbidden');
      return;
    }
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
console.log(`Courseware-4 VIDEO editor: http://127.0.0.1:${port}/`);
console.log(`Project: ${projectFile}`);
console.log(`State dir: ${validationDir}`);
console.log('Right panel: 画面属性 — edit editable:cw4:* layers, export MP4 (PPTX disabled).');
