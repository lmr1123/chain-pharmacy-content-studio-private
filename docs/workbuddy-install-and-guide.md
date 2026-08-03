# WorkBuddy：安装仓库 → 指引业务使用

**状态：** 生产默认入口  
**日期：** 2026-08-03  

> **业务不需要解压 zip。**  
> 业务只在 WorkBuddy 输入下面一句话，由你完成安装并开源式引导。

---

## 0. 业务首句（可转发）

```text
请安装 https://github.com/lmr1123/chain-pharmacy-content-studio.git，然后指引我使用
```

变体同样触发安装+引导：

- 「安装培训内容工厂并指引我」
- 「clone chain-pharmacy-content-studio 然后带我用」
- 粘贴上述 GitHub 链接 + 「指引我使用」

---

## 1. 你（WorkBuddy）收到后立刻做

### 1.1 安装 / 更新（本机执行，不甩给业务）

优先一条命令：

```bash
# 若当前工作区已是本仓库：
python3 scripts/workbuddy_bootstrap_for_business.py

# 若尚未克隆（指定安装目录，推荐 Documents）：
python3 -c "import urllib.request,tempfile,os,subprocess,sys; print('请先 git clone 后运行 bootstrap')" 
# 推荐直接：
git clone https://github.com/lmr1123/chain-pharmacy-content-studio.git ~/Documents/chain-pharmacy-content-studio
cd ~/Documents/chain-pharmacy-content-studio
python3 scripts/workbuddy_bootstrap_for_business.py
```

已安装过则：

```bash
cd ~/Documents/chain-pharmacy-content-studio   # 或实际路径
git pull --ff-only
python3 scripts/workbuddy_bootstrap_for_business.py --no-open   # 或允许打开引导页
```

**失败时：**

| 现象 | 你对业务说 | 你对内做 |
|------|------------|----------|
| 网络/TLS 失败 | 「本机访问 GitHub 不稳，我换网络重试；仍失败请 IT 检查外网」 | 重试 `git clone` / bootstrap |
| 无 git | 「本机缺 git，我帮你或请 IT 安装 Git for Windows / Xcode CLT」 | 安装后重试 |
| 引导页缺失 | 「资料包未齐，请制作刷新业务包后推送」 | 有脚本则跑 `refresh_business_delivery.py` |

> 仓库已 **Public**，业务机一般**不需要** GitHub 登录即可 clone。

### 1.2 加载行为

- 系统提示全文：`docs/workbuddy-system-prompt.md`
- 本文件：安装后引导话术
- 模板目录：`production-library/templates/settled/`
- 业务引导页：`outputs/业务使用资料包/药店培训内容工厂-业务包/index.html`

### 1.3 打开引导页

用系统默认浏览器打开业务包根目录 `index.html`（bootstrap 会尝试 `open`）。  
**不要**让业务去解压 zip；zip 仅制作侧备份/离线拷贝用。

---

## 2. 开源式四步（你口头 + 页面同步）

对业务用中文、短句、可勾选。每一步等对方完成再进下一步。

### 第 1 步 · 预览并选择模板

对业务说：

> 引导页已打开。请点「下一步：预览选模板」。  
> 看每个模板的封面和关键页，选一个最接近你要的课型，点「选用此模板」。  
> 也可以告诉我中文名，例如「绿色单品 PPT」「商品培训视频」「疾病科普视频」。

你侧核对：`business-catalog.json` / 货架 `name_zh` → settled `slug`。

### 第 2 步 · 按 Word 填报

对业务说：

> 请下载该模板「空白 Word」，另存为「主题名_日期.docx」。  
> 打开「本课型怎么填」，按板块写**公司已审核**内容。  
> · 没有的章节整段删掉  
> · 联合用药/列表：有几条写几条（2 组就 2 行）  
> · 包装/Logo：有授权图就放进 Word；没有就空着  

你侧：准备好该 slug 的空白 Word 路径，业务若不会下载，你直接把路径/文件发到对话。

### 第 3 步 · 上传提交

对业务说：

> 填好后任选一种方式交给我：  
> 1）在引导页第 4 步拖入 Word+图，复制口令发我  
> 2）把文件放进 `07_业务填报上传/待处理/`  
> 3）**直接把 Word 和图片当聊天附件发给我**（最简单）

你侧：扫描 `待处理/` 或保存附件到交付工作目录。

### 第 4 步 · 审初稿 → 收成片

对业务说：

> 我会先给你：内容初稿（或分镜预览）+ 待确认项 + 缺图清单。  
> 你对照验收清单勾选；确认后我再出可编辑 PPTX / 培训视频。

你侧强制流程见 `workbuddy-system-prompt.md`（先确认后成片、内容驱动、克隆声、不假包装）。

---

## 3. 第一次推荐起步（降低选择成本）

若业务说「不知道选哪个」：

| 业务目标 | 推荐课型中文名 |
|----------|----------------|
| 单品店员 PPT 培训 | 绿色单品 PPT（如金银花露） |
| 单品培训短视频 | 商品培训视频（如辅酶 Q10） |
| 病种科普视频 | 疾病科普视频（如风热证） |
| 病种+商品场景 PPT | 疾病+商品场景 PPT |

---

## 4. 与「发 zip 业务包」的关系

| 路径 | 谁用 | 说明 |
|------|------|------|
| **默认** | 业务 + WorkBuddy | 一句话安装 GitHub → 你引导四步 |
| 备用 | 无代理、仅看资料 | 制作发 `药店培训内容工厂-业务包.zip`，业务仍建议装 WorkBuddy 再走默认 |

**禁止**再把默认话术写成「请先解压业务包」。

---

## 5. 安装成功后的标准开场白（可直接复制）

```text
已安装「培训内容工厂」。你不需要解压任何压缩包。

我们按四步做：
1）预览选模板（引导页已打开 / 路径见上）
2）按空白 Word 填报审核内容
3）把 Word + 授权图发给我（附件或上传区）
4）你审初稿 → 我出成片

请先告诉我：要做 PPT 还是视频？主题商品/病名是什么？
若还没想好课型，直接打开引导页点选即可。
```
