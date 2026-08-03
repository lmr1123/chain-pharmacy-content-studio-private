# 业务机 WorkBuddy · 视频课件首次自检清单

**用途：** 业务在 WorkBuddy **自己出视频**前，由**代理在业务机执行**下面命令确认环境（不要让业务敲命令）。  
**PPT 出片** 不强制；**商品培训视频 / 疾病科普视频 full 重渲** 必须过。

仓库根目录 `$REPO`（常见 `~/Documents/chain-pharmacy-content-studio`）。

---

## 0. 一次准备

```bash
cd $REPO
git pull --ff-only
# 系统提示请用最新 docs/workbuddy-system-prompt.md 全文重贴到 WorkBuddy
```

---

## 五条自检（按顺序）

### ① 代码与引导页

```bash
cd $REPO && git rev-parse --short HEAD && \
  test -f scripts/generate_business_video.py && \
  test -f scripts/business_video_product_full.py && \
  test -f scripts/business_video_health_full.py && \
  test -f poc/gold-sample/scripts/render-health-segment.mjs && \
  test -f docs/workbuddy-system-prompt.md && echo "OK code"
```

期望：打印短 commit + `OK code`。

### ② ffmpeg（需 lavfi，推荐 Homebrew）

```bash
/opt/homebrew/bin/ffmpeg -hide_banner -demuxers 2>&1 | grep -q lavfi && echo "OK ffmpeg" || echo "FAIL ffmpeg: 请 brew install ffmpeg"
```

期望：`OK ffmpeg`。  
失败则视频重渲后处理易挂。

### ③ 克隆语音包 + Qwen TTS 环境

```bash
cd $REPO && test -f production-library/voices/reference-pharmacist-qwen-v1/prompt.wav && \
  .venv-qwen-tts/bin/python -c "from mlx_audio.tts.utils import load_model; print('OK tts')" 2>/dev/null || \
  echo "FAIL tts: 需 .venv-qwen-tts（含 mlx_audio / Qwen3-TTS）"
```

期望：`OK tts`。  
无此环境：只能 `--mode plan` 出分镜，**不能** full 出正式旁白视频。

### ④ 商品视频渲染依赖（Node）

```bash
cd $REPO/poc/gold-sample && test -d node_modules && test -f scripts/render-product-segment.mjs && echo "OK node" || \
  (npm install && echo "OK node after install")
```

期望：`OK node` 或 install 后成功。

### ⑤ 最小出片冒烟（约 2～4 分钟，会真出 MP4）

**商品培训视频：**

```bash
cd $REPO
cat > /tmp/wb-video-smoke.json <<'EOF'
{
  "theme": "自检演示品",
  "sections": [
    {"title": "为什么要了解", "narration": "本片仅作业务机环境自检，不代表正式医学内容。"},
    {"title": "商品基础信息", "narration": "自检演示品，规格以公司审核资料为准。"},
    {"title": "核心讲解", "narration": "自检通过后即可用真实审核稿换主题出片。"},
    {"title": "核心功效", "narration": "1、自检要点甲。2、自检要点乙。"},
    {"title": "产品特点", "narration": "1、环境可用。2、依赖齐全。3、可正式出片。"},
    {"title": "适宜人群", "narration": "仅用于门店内部培训系统自检。"},
    {"title": "联合用药", "narration": "1、方案甲加自检演示品。2、方案乙加自检演示品。"},
    {"title": "总结", "narration": "自检完成，请改用真实审核内容再出正式片。"}
  ]
}
EOF

.venv-qwen-tts/bin/python scripts/generate_business_video.py \
  --template product \
  --sections-json /tmp/wb-video-smoke.json \
  --with-tts --with-mp4 \
  --slug wb-first-check
```

期望：结束 JSON 里 `"ok": true`、`"mp4": true`，并存在：

```text
outputs/business-video-runs/wb-first-check/*_商品培训视频_v1.mp4
```

**疾病科普视频（可选 · 7 段，约 4～8 分钟）：**

```bash
cat > /tmp/wb-health-smoke.json <<'EOF'
{
  "theme": "自检演示证",
  "sections": [
    {"title": "开场", "narration": "中医基础知识自检演示证。"},
    {"title": "基础认知", "narration": "本片仅作业务机环境自检，画面与旁白应出现自检演示证。"},
    {"title": "病因机理", "narration": "自检演示：外邪入侵导致不适。"},
    {"title": "典型症状", "narration": "一、表现甲。二、表现乙。三、表现丙。"},
    {"title": "调理建议", "narration": "核心是辨证调理。可用常用食材配合。"},
    {"title": "用药建议", "narration": "注意休息、多喝温水、饮食清淡、及时就医。"},
    {"title": "总结", "narration": "自检完成，请改用真实审核病种内容再出正式片。"}
  ]
}
EOF

.venv-qwen-tts/bin/python scripts/generate_business_video.py \
  --template health \
  --sections-json /tmp/wb-health-smoke.json \
  --with-tts --with-mp4 \
  --slug wb-health-first-check
```

期望：

```text
outputs/business-video-runs/wb-health-first-check/*_疾病科普视频_v1.mp4
```

---

## 判定

| 结果 | 含义 |
|------|------|
| ①～⑤ 全过 | **可以**让业务在 WorkBuddy 上生成商品培训视频 |
| ①～⑤ + 疾病科普冒烟 | **可以**生成疾病科普视频（风热金样 full 重渲） |
| ①②④ 过、③ 挂 | 可 plan / 出 PPT；视频正式旁白需先装 TTS venv |
| ⑤ 挂 | 把终端报错留给制作侧；勿对业务假装已出片 |

---

## 自检通过后 · 业务怎么用（自助）

业务只说话，代理出片：

```text
我要用【商品培训视频】，商品是【真实商品名】。内容……请生成培训视频。
```

```text
我要用【疾病科普视频】，主题是【病名】。内容……请生成培训视频。
```

代理：整理 sections → `--mode full --with-tts --with-mp4` → 回传 MP4 路径。  
禁止说「找制作」「只能换声」「full 未接入」。

PPT 仍走既有 generator，不走本清单 ⑤。
---

## 关联

- 系统提示：`docs/workbuddy-system-prompt.md`  
- 安装与三步话术：`docs/workbuddy-install-and-guide.md`  
- 商品 full：`scripts/generate_business_video.py` + `scripts/business_video_product_full.py`  
- 疾病科普 full：`scripts/business_video_health_full.py` + `poc/gold-sample/scripts/render-health-segment.mjs`  
