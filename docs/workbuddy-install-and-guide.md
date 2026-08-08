# WorkBuddy：安装仓库 → 业务自己出片

**状态：** 生产默认入口  
**日期：** 2026-08-04  

> **目标：** 业务在 WorkBuddy 对话里自己生成 PPT / 商品视频 / 疾病科普视频。  
> 制作不代出正常 settled 单。安装后对业务只讲 **3 步**。

---

## 0. 业务首句

```text
请安装 https://github.com/lmr1123/chain-pharmacy-content-studio.git，然后指引我使用
```

---

## 1. 你（WorkBuddy）立刻做

```bash
# 首次：Public 仅为脱敏安装器
git clone https://github.com/lmr1123/chain-pharmacy-content-studio.git \
  ~/Documents/chain-pharmacy-content-studio-installer
cd ~/Documents/chain-pharmacy-content-studio-installer
python3 scripts/install_private_studio.py

# 已安装完整 Private 生产仓
cd ~/Documents/chain-pharmacy-content-studio-private
git pull --ff-only
python3 scripts/workbuddy_bootstrap_for_business.py
```

Public installer 会先检查当前用户的 GitHub 登录状态，以及
`lmr1123/chain-pharmacy-content-studio-private` 的 `read` 权限；通过后才拉取/更新完整 Private 生产仓并调用 bootstrap。Public 仓不含模板、预览、声纹、业务包或生成器，不能单独出片。未登录或未获授权时，说明具体权限卡点并停止；禁止把 token 写入 URL/日志，禁止公共镜像，禁止回退公开 ZIP。

Private bootstrap 会优先打开带本机能力状态、且不写入 Git 的 `index.local.html`；刷新失败才回退 Private checkout 内的固定 `index.html`。
系统提示（须全文重贴到 WorkBuddy）：`docs/workbuddy-system-prompt.md`

**首次出视频前**（你执行，不让业务敲命令）：  
`docs/workbuddy-video-first-check.md`  
PPT 不强制；商品/疾病科普视频 full 重渲必须过。

---

## 2. 标准开场白（安装成功后 · 整段对业务说）

```text
你好！培训内容工厂已装好。你在本对话就能出课件和视频，三步做完：

第 1 步 · 看模板
引导页已打开。点卡片可看预览，再点「选用此模板」；也可以直接告诉我课型名。

第 2 步 · 输入培训内容（PPT 或视频都行）
例如：
· PPT：「整理可可康灵芝胶囊…你先整理再生成 ppt」
· 商品培训课件3：「按课件3模板，整理××商品：卖点…、人群…、联合用药2组…，生成可编辑课件」
· 疾病科普视频：「我要用疾病科普视频，主题是感冒。症状…病因…调理…用药注意…请生成培训视频」
· 商品培训视频：「我要用商品培训视频，商品是××。功效/特点/人群/联合用药…请生成培训视频」
· 数字人侧讲：「这个课件用数字人模式。请先整理旁白脚本和数字人页清单给我确认，确认前不要生成数字人」
· 健康科普 Seedance（生活避险）：「做 Seedance 生活科普，主题是×××。先出脚本确认」
· 九宫格原版：「做九宫格原版，主题×××，知识点…先出六段口播」
· 九宫格合规版：「做九宫格合规版无医疗，主题×××，受众…习惯点…」

第 3 步 · 下载与修改
我把成片路径发给你；要改就说「第二页…改成…」或「把症状段改成…再出一版」。

【若选用数字人模式 · 多一道确认】
我会先给你「全课旁白脚本 + 哪些页有数字人」。
你确认页码和文案、并说「可以生成」后，我才生成数字人（确认前不产生数字人费用）。
说明：业务包 08_数字人侧讲模式/README.md

【若选用健康科普 Seedance · 多一道确认】
我会先给你「5 拍科普脚本 + 口播」。
你确认后说「可以出 Seedance 提示词」，我再给可复制到即梦/Seedance 的分段提示词和视频号发布文案。
说明：业务包 09_健康科普Seedance模式/README.md（这不是店内「疾病科普培训片」）

【若选用九宫格原版 · 多一道确认】
我会先给你「60 秒六段口播」（林医生 + 王大爷）。
你确认后说「可以出九宫格和视频提示词」。说明：10_健康科普九宫格模式/

【若选用九宫格合规版 · 多一道确认】
我会先给你脱敏说明 + 六段口播（小林，无医生医院）。
你确认后说「可以出九宫格合规版提示词」。说明：11_健康科普九宫格合规版/

现在可以从第 1 步选模板，或直接发第 2 步内容给我。
```

---

## 3. 你侧执行（不对业务念）

| 步 | 业务说/做 | 你做 |
|----|-----------|------|
| 0 | （安装后） | `python3 scripts/probe_production_env.py`；记 TTS/渲染能力 |
| 1 | 看引导页 / 说课型名 | 打开 bootstrap 返回的本机门户（回退时为 index.html）；锁定 settled 模板；读 manifest.voice_id |
| 2 | 发商品/病名 + 要点 | 整理内容 → **本机出片**（PPT generator / `generate_business_courseware.py` / `generate_business_video.py`） |
| 3 | 下载或改稿指令 | 给成片路径 + gap；按指令改后重出 |

**课件3（优先 PPTX）：**

```bash
python3 scripts/probe_production_env.py
python3 scripts/generate_business_courseware.py \
  --template courseware3 --theme <theme目录> --skip-tts
# 有 TTS 再去掉 --skip-tts；无环境脚本会诚实降级
```

**视频（业务自助核心）：**

```bash
# 疾病科普 · WorkBuddy 先生成主题包、补齐内容/画面并完成哈希审批（禁止 audio-shell）
python3 scripts/build_health_theme_package.py \
  --theme <主题> --sections-json <你整理的json> --out-dir <theme-package目录>
.venv-qwen-tts/bin/python scripts/generate_business_video.py \
  --template health --theme-package <theme-package目录> --with-tts --with-mp4

# 商品培训 · 先出审批请求，业务确认内容与包装授权后再正式出片
python3 scripts/generate_business_video.py \
  --template product --mode plan --sections-json <json> \
  --product-image <业务提供的包装图>
.venv-qwen-tts/bin/python scripts/generate_business_video.py \
  --template product --sections-json <json> --with-tts --with-mp4 \
  --product-image <业务提供并确认授权的包装图> \
  --product-approval <已批准JSON>
```

回传业务：`*_疾病科普视频_v1.mp4` 或 `*_商品培训视频_v1.mp4` + storyboard。  
自检：`run-status.json` 里 method 须含 `segment-rerender`，不能是 `audio-shell`。

缺箭头/勾叉等小符号：内部按 Koboyo 本机匹配，**不要**让业务找图标。

禁止对业务说：解压 zip、起端口、找制作代出片（正常 settled 单）。

---

## 4. 推荐课型（业务说不清时）

| 目标 | 课型中文名 | 谁出片 |
|------|------------|--------|
| 单品店员 PPT | 绿色单品 PPT（如金银花露） | **业务机 WorkBuddy** |
| 疾病健康知识 PPT | 疾病健康知识培训 PPT（参课蓝） | **业务机 WorkBuddy** |
| 单品培训视频 | 商品培训视频（如辅酶 Q10） | **业务机 WorkBuddy full 重渲** |
| 病种科普视频 | 疾病科普视频（如风热证） | **业务机 WorkBuddy full 重渲** |
| 视频号生活避险科普 | 健康科普 Seedance | **提示词复制到即梦/Seedance**（本机 scaffold） |
| 中老年 60s 九宫格（可卡通医生） | 九宫格原版 | scaffold `jiugongge-health-edu-v1` |
| 视频号严格无医疗九宫格 | 九宫格合规版 | scaffold `jiugongge-health-edu-compliance-v1` |
