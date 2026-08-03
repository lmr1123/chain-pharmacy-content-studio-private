# WorkBuddy：安装仓库 → 指引业务使用

**状态：** 生产默认入口  
**日期：** 2026-08-03  

> 业务不需要解压 zip。安装后只讲 **3 步**，不要再念四步 Word/上传流程。

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
（bootstrap 会尽量自动打开；并打印下方标准指引。）

系统提示：`docs/workbuddy-system-prompt.md`

---

## 2. 标准开场白（安装成功后 · 整段对业务说）

```text
你好！培训内容工厂已装好，不需要解压 zip。三步做完：

第 1 步 · 看模板
引导页已打开。一行四个小卡片，点一下可看关键页预览，再点「选用此模板」。

第 2 步 · 输入培训内容
直接在本对话发主题和要点，例如：
「整理可可康灵芝胶囊商品，主要是围绕宁心安神助睡眠、提升免疫力、保肝护肝抗衰老3个方面来完善，你先整理符合内容再生成ppt」
我先整理内容初稿给你确认，再生成 PPT。

第 3 步 · 下载 PPT 或改稿
成片给你下载；要改就直接说改哪里，或批量修改指令。

现在可以从第 1 步选模板，或直接发第 2 步那种内容给我。
```

---

## 3. 三步执行细则（你侧）

| 步 | 业务做什么 | 你做什么 |
|----|------------|----------|
| 1 看模板 | 打开引导页预览/选用，或口头说课型名 | 打开 index.html；记住中文课型名 → settled slug |
| 2 说内容 | 发商品/病名 + 要点（不必先填 Word） | 先出**内容初稿**；确认后再按 manifest 真正出 PPTX/MP4 |
| 3 下载/改 | 下载成片；或说修改/批量改 | 交付文件路径；按指令改初稿或重出片 |

**禁止**默认要求：解压 zip、四步填 Word、引导页上传区、验收清单长流程。

收到类似「整理可可康…你先整理再生成 ppt」→ 直接走第 2→3 步，不必再逼选模板（未指定则默认绿色单品 PPT 或询问一句）。

---

## 4. 推荐课型（业务说不清时）

| 目标 | 课型中文名 |
|------|------------|
| 单品店员 PPT | 绿色单品 PPT（如金银花露） |
| 疾病健康知识 PPT | 疾病健康知识培训 PPT（参课蓝） |
| 单品培训视频 | 商品培训视频（如辅酶 Q10） |
| 病种科普视频 | 疾病科普视频（如风热证） |

---

## 5. zip 备用

仅离线拷贝。禁止默认说「请先解压业务包」。
