# 业务 + WorkBuddy：今天怎么用

**默认协作模型（已锁定）：**

> **业务**负责内容与确认 · **WorkBuddy**负责安装工程、按 settled 模板出初稿与成片。  
> **业务不需要解压任何 zip。**  
> 不是「业务独自双击出片」，也不是「业务只能交材料、再等制作手工做」。  
> **标准路径不经过制作返修**；制作只处理异常/新页型/编辑器级返修。

**业务首句（复制到 WorkBuddy）：**

```text
请安装 https://github.com/lmr1123/chain-pharmacy-content-studio.git，然后指引我使用
```

仓库已 **Public**：业务机一般无需 GitHub 账号/权限即可安装。  
国内直连 GitHub 可能慢或超时——WorkBuddy 安装脚本会自动试国内可用镜像；仍失败再换网络或用业务包 zip 备用。

**WorkBuddy 侧：** `docs/workbuddy-install-and-guide.md` + `docs/workbuddy-system-prompt.md`  
**刷新业务包（制作）：** `python3 scripts/refresh_business_delivery.py`

---

## 分工（一句话）

| 角色 | 做什么 | 不做什么 |
|------|--------|----------|
| **业务** | 在 WorkBuddy 说安装句；在引导下预览选模板、填 Word、交授权图、审初稿、点确认、收成片 | 自己解压 zip、装 Node、起端口、调 TTS、改坐标/图层 |
| **WorkBuddy** | clone/更新仓库、打开引导页、逐步指引、锁定模板、解析 Word、内容驱动、列缺口、确认后出 PPTX/MP4 | 把正常 settled 单甩回「请找制作」；编造医学结论；假包装；系统机器人音色 |

---

## 端到端（双方一起完成交付）

```text
业务                              WorkBuddy
────                              ────────
① 打开 WorkBuddy，粘贴安装句  →
                                  ② git clone / pull + bootstrap
                                  ③ 打开 index.html，开始四步指引
④ 预览选模板
⑤ 填空白 Word + 授权图
⑥ 附件或上传区提交            →
                                  ⑦ 锁定 template / style_pack / voice
                                  ⑧ 解析内容（N 条→N 行）
                                  ⑨ 交「内容初稿 + 缺口」或「分镜 + 缺口」
⑩ 审阅、改文案、确认          →
                                  ⑪ 生成终稿 PPTX 和/或 MP4
⑫ 成片归档 / 门店使用
```

业务**不需要**自己点生成器、也**不需要**解压包；**需要** WorkBuddy 把安装与 ⑦～⑪ 做完。

---

## 业务侧操作（你 · 一句话启动）

1. 打开 **WorkBuddy**  
2. 输入：

```text
请安装 https://github.com/lmr1123/chain-pharmacy-content-studio.git，然后指引我使用
```

3. 在打开的网页上**选模板**（一行四个小卡片，点开看关键页截图）  
4. 回 WorkBuddy **直接说内容**，例如：  
   `整理可可康灵芝胶囊，围绕宁心安神助睡眠、提升免疫力、保肝护肝抗衰老，你先整理符合内容再生成ppt`  
5. 确认内容初稿后，WorkBuddy 生成 PPT / 视频  

### 你有权这样要求 WorkBuddy

- 「你先整理符合模板的内容初稿，我确认后再生成 ppt」  
- 「联合用药我只写了 2 组，按 2 行排，不要空第三行」  
- 「没包装图就槽位待补，不要仿包装」

---

## WorkBuddy 侧必须做到（代理）

1. 识别安装句 → 跑 `scripts/workbuddy_bootstrap_for_business.py`（或等价 clone+打开引导页）  
2. 按 `docs/workbuddy-install-and-guide.md` 逐步指引，不要丢一堆路径让业务自己摸  
3. 用 `business-catalog.json` 把中文课型名落到 settled slug  
4. 列表/联合用药用 `scripts/content_driven_rules.py`  
5. **确认前**：只交初稿/分镜 + 缺口  
6. **确认后**：按 manifest generator / 既有脚本真正产出 PPTX 或 MP4  
7. 交付目录写清；带 `template_id` / `style_pack_id` / `voice_id` 追溯  

正常换主题 **禁止**停在「请制作同事处理」。  
仅当：新页型全库没有、金样冻结、或渲染环境缺失时，才升级制作并**明确告知业务卡点**。

---

## 备用：无 WorkBuddy 时

制作可另发 `outputs/业务使用资料包/药店培训内容工厂-业务包.zip` 供离线预览 Word。  
**正式交付仍建议装 WorkBuddy 走默认安装句**，否则无法在本机自动出成片。

---

## 和「一键无人值守」的区别

- **我们做的：** 业务一句话 → WorkBuddy 安装并引导 → 对话协作高质量交付。  
- **我们没承诺的：** 业务电脑上没有任何代理、只双击 Word 就出片。
