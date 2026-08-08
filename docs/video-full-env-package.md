# 商品正式 MP4 环境包（video-full）

**状态：** 2026-08-09 正式入口  
**业务路线：** `product-mp4-full-v1`（内部商品培训 · 完整 MP4）  
**健康/疾病视频自助：** 另案专项，不在本文。

---

## 一句话

正式商品视频 = **审核脚本 + 授权包装图** + 本机三件套：

1. **旁白 TTS**（`.venv-qwen-tts`，参考药师音色）  
2. **视频 kit**（Revideo 工程：`production-library/engines/video-revideo-runtime-v1/kit`）  
3. **系统工具**（Node + ffmpeg/ffprobe）

缺一件就诚实失败，不假装出正式成片。

---

## 快速检查

```bash
python3 scripts/video_full_env.py check
python3 scripts/business_doctor.py --profile video-full
python3 scripts/probe_production_env.py --require video-full
```

通过后再：

```bash
python3 scripts/business_job.py new \
  --route product-mp4-full-v1 \
  --theme <商品名> \
  --notes '...' \
  --product-image <授权包装图路径> \
  --auto-draft
# approve content + product_image → render
```

---

## 开发机：打离线 kit 包

在已能渲染的机器上：

```bash
# 含 node_modules（推荐给业务机，体积大）
python3 scripts/video_full_env.py package \
  --out ~/Desktop/video-runtime-kit-v1.tgz

# 不含 node_modules（仅源码结构，目标机需另装依赖）
python3 scripts/video_full_env.py package \
  --out ~/Desktop/video-runtime-kit-src.tgz \
  --without-node-modules
```

包内排除 `.mp4` / `dist` 等产物；**不含** `.venv-qwen-tts`（TTS 环境本机装，不随 Git/公共包乱传）。

---

## 业务机 / 干净机：恢复 kit

```bash
# 1) 先试本地 soft-repair（有历史 poc/gold-sample 时）
python3 scripts/video_full_env.py soft-repair

# 2) 或从授权离线包恢复到正式路径
python3 scripts/video_full_env.py restore \
  --from ~/Desktop/video-runtime-kit-v1.tgz \
  --force

# 3) 再 check
python3 scripts/video_full_env.py check
```

恢复目标固定为：

`production-library/engines/video-revideo-runtime-v1/kit`

业务代码只认 `scripts/video_runtime.py` 解析结果，不要再写死 `poc/gold-sample`。

---

## TTS 环境（旁白）

- 路径：仓库根 `.venv-qwen-tts`  
- 验证：

```bash
.venv-qwen-tts/bin/python -c \
  "from mlx_audio.tts.utils import load_model; print('OK')"
```

- 声纹：`production-library/voices/reference-pharmacist-qwen-v1/`（Private 资产）  
- **禁止**系统 `say` / edge-tts 冒充正式旁白  

细节见 `docs/workbuddy-video-first-check.md`。

---

## 与 bootstrap 的关系

```bash
python3 scripts/workbuddy_bootstrap_for_business.py --profile video-full --no-open
```

bootstrap 会 soft-repair kit 链接并调用 doctor；**不会**自动联网装 TTS。  
离线 kit 用 `video_full_env.py restore` 补齐。

---

## 验收口径（工程师）

| 检查 | 期望 |
|------|------|
| `video_full_env.py check` | exit 0，`video_full=true` |
| kit | formal 路径存在且含 render 脚本 + src + node_modules |
| TTS | mlx_audio.tts 可 import |
| 业务任务 | content + product_image 审批后 render 可交付 MP4 |

业务侧现场验片另排；健康视频开放另专项。
