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
# 首次
git clone https://github.com/lmr1123/chain-pharmacy-content-studio.git ~/Documents/chain-pharmacy-content-studio
cd ~/Documents/chain-pharmacy-content-studio
python3 scripts/workbuddy_bootstrap_for_business.py

# 已有仓库
cd ~/Documents/chain-pharmacy-content-studio
git pull --ff-only
python3 scripts/workbuddy_bootstrap_for_business.py
```

打开引导页：`outputs/业务使用资料包/药店培训内容工厂-业务包/index.html`  
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
· 疾病科普视频：「我要用疾病科普视频，主题是感冒。症状…病因…调理…用药注意…请生成培训视频」
· 商品培训视频：「我要用商品培训视频，商品是××。功效/特点/人群/联合用药…请生成培训视频」

第 3 步 · 下载与修改
我把成片路径发给你；要改就说「第二页…改成…」或「把症状段改成…再出一版」。

现在可以从第 1 步选模板，或直接发第 2 步内容给我。
```

---

## 3. 你侧执行（不对业务念）

| 步 | 业务说/做 | 你做 |
|----|-----------|------|
| 1 | 看引导页 / 说课型名 | 打开 index.html；锁定 settled 模板 |
| 2 | 发商品/病名 + 要点 | 整理 sections → **本机 full 出片**（PPT generator 或 `generate_business_video.py`） |
| 3 | 下载或改稿指令 | 给成片路径；按指令改内容后重出 |

**视频（业务自助核心）：**

```bash
# 疾病科普 · 画面随病名换（禁止 audio-shell）
.venv-qwen-tts/bin/python scripts/generate_business_video.py \
  --template health --sections-json <你整理的json> --with-tts --with-mp4

# 商品培训 · 画面随商品换
.venv-qwen-tts/bin/python scripts/generate_business_video.py \
  --template product --sections-json <json> --with-tts --with-mp4 \
  --product-image <授权包装图可选>
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
