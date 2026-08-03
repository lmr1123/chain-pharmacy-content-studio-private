# WorkBuddy：安装仓库 → 指引业务使用

**状态：** 生产默认入口  
**日期：** 2026-08-03  

> **业务不需要解压 zip。**  
> 业务只在 WorkBuddy 输入安装句；安装后打开**精简引导页**选模板，再在聊天里说内容出片。

---

## 0. 业务首句（可转发）

```text
请安装 https://github.com/lmr1123/chain-pharmacy-content-studio.git，然后指引我使用
```

---

## 1. 你（WorkBuddy）收到后立刻做

### 1.1 安装 / 更新

```bash
git clone https://github.com/lmr1123/chain-pharmacy-content-studio.git ~/Documents/chain-pharmacy-content-studio
cd ~/Documents/chain-pharmacy-content-studio
python3 scripts/workbuddy_bootstrap_for_business.py
```

已安装：

```bash
cd ~/Documents/chain-pharmacy-content-studio
git pull --ff-only
python3 scripts/workbuddy_bootstrap_for_business.py
```

国内 clone 失败时 bootstrap 会自动试镜像；仍失败再换网络或 zip 备用。

### 1.2 打开引导页

`outputs/业务使用资料包/药店培训内容工厂-业务包/index.html`  

**页面只有两块：**

1. **模板预览与选择**（一行 4 个小卡片；点开看关键页大图）  
2. **填报真实示例**（下载对照）

不要再按「四步填 Word / 上传区 / 验收清单」堆话术。

### 1.3 系统提示

`docs/workbuddy-system-prompt.md`

---

## 2. 标准业务路径（对话式）

```text
① 安装句
② 网页选模板（或直接告诉你中文课型名）
③ 聊天描述商品/疾病要点
④ 你整理「内容初稿」→ 业务确认
⑤ 你生成 PPTX / MP4
```

### 对业务说（安装成功后开场白）

```text
已安装「培训内容工厂」。引导页已打开。

请在网页上点一个模板，看关键页截图后点「选用」。
也可以直接告诉我课型，例如「绿色单品 PPT」。

然后像这样把内容发给我，例如：
「整理可可康灵芝胶囊，围绕宁心安神助睡眠、提升免疫力、保肝护肝抗衰老，
你先整理符合内容再生成 ppt」

我会先给内容初稿，你确认后再出可编辑 PPT。
```

### 收到「整理某某商品…先整理再生成」时

1. 锁定模板（未选则默认/询问：商品 PPT 优先「绿色单品 PPT」）  
2. 按 settled 框架整理**内容初稿**（有几条写几条；不编造；无包装标缺口）  
3. 请业务确认  
4. 确认后按 manifest generator **真正出 PPTX**  

**不要**要求业务先会写完整 Word 才开工；Word 仅可选对照。

---

## 3. 推荐课型（业务说不清时）

| 业务目标 | 课型中文名 |
|----------|------------|
| 单品店员 PPT | 绿色单品 PPT（如金银花露） |
| 疾病健康知识 PPT | 疾病健康知识培训 PPT（参课蓝） |
| 单品培训视频 | 商品培训视频（如辅酶 Q10） |
| 病种科普视频 | 疾病科普视频（如风热证） |

---

## 4. zip 备用

仅离线拷贝用。**禁止**默认说「请先解压业务包」。
