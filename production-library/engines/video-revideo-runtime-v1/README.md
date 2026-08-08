# video-revideo-runtime-v1

商品培训 / 疾病科普 **full MP4** 分段渲染的正式 runtime 入口。

## 解析顺序

1. `production-library/engines/video-revideo-runtime-v1/kit`（本引擎 kit，可 symlink）
2. 回退：`poc/gold-sample`（历史路径，仅兼容）

业务代码应通过 `scripts/video_runtime.py` 解析，不要硬编码 `poc/gold-sample`。

## 目录

| 路径 | 说明 |
|------|------|
| `runtime-manifest.json` | 必需文件、分段 id、入口脚本 |
| `scripts/render-*-segment.mjs` | 正式入口副本（与 kit 内脚本同步） |
| `kit/` | 完整 Revideo 工程（src/public/json/node_modules） |

## 本地 soft-repair / 离线包

```bash
# 探测 TTS + kit + ffmpeg（商品正式视频）
python3 scripts/video_full_env.py check

# kit 缺失且本机有 poc/gold-sample 时：symlink soft-repair
python3 scripts/video_full_env.py soft-repair

# 开发机打包（可含 node_modules）
python3 scripts/video_full_env.py package --out /tmp/video-runtime-kit.tgz

# 业务机/干净机从授权包恢复到 formal kit 路径
python3 scripts/video_full_env.py restore --from /tmp/video-runtime-kit.tgz --force
```

bootstrap 在 `kit` 缺失且 legacy 存在时，也会创建 `kit → ../../../poc/gold-sample` 链接。  
完整说明：`docs/video-full-env-package.md`。

## 探测

```bash
python3 scripts/business_doctor.py --profile video-full
python3 scripts/probe_production_env.py --require video-full
python3 scripts/video_full_env.py check
```
