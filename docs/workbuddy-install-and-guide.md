# WorkBuddy：安装仓库 → 指引业务使用

**状态：** 生产默认入口  
**日期：** 2026-08-03  

> 安装后对业务只讲 **3 步**。不要念 zip、不要念「先初稿再确认」等内部流程。

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
系统提示：`docs/workbuddy-system-prompt.md`

**首次出「商品培训视频」前**（业务机环境自检 5 条命令）：  
`docs/workbuddy-video-first-check.md`  
（PPT 不强制；视频 full 重渲必须过。）

---

## 2. 标准开场白（安装成功后 · 整段对业务说）

```text
你好！培训内容工厂已装好。三步做完：

第 1 步 · 看模板
引导页已打开（路径见上）。一行四个小卡片，点一下可看关键页预览，再点「选用此模板」。

第 2 步 · 输入培训内容
直接在本对话发主题和要点，例如：
「整理可可康灵芝胶囊商品，主要是围绕宁心安神助睡眠、提升免疫力、保肝护肝抗衰老3个方面来完善，你先整理符合内容再生成ppt」

第 3 步 · 下载与修改
可下载 PPT 修改，或输入指令批量修改，例如：
「第二页卖点改成…」「批量把联合用药改成 2 条」

现在可以从第 1 步选模板，或直接发第 2 步那种内容给我。
```

---

## 3. 你侧执行（不对业务念）

| 步 | 业务说/做 | 你做 |
|----|-----------|------|
| 1 | 看引导页 / 说课型名 | 打开 index.html；锁定 settled 模板 |
| 2 | 发商品/病名 + 要点 | 内部先整理内容再出片；有附件则解析 |
| 3 | 下载或改稿指令 | 给 PPT 路径；按指令改稿/重出 |

禁止默认对业务说：解压 zip、先填完整 Word、引导页上传区、验收清单长流程。

---

## 4. 推荐课型（业务说不清时）

| 目标 | 课型中文名 |
|------|------------|
| 单品店员 PPT | 绿色单品 PPT（如金银花露） |
| 疾病健康知识 PPT | 疾病健康知识培训 PPT（参课蓝） |
| 单品培训视频 | 商品培训视频（如辅酶 Q10） |
| 病种科普视频 | 疾病科普视频（如风热证） |
