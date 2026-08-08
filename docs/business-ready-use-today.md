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

这个 URL 是**脱敏 Public 安装入口**，不是生产仓库。业务机需先用 GitHub CLI 登录，且当前账号已获 Private production 的 `read` 权限；未登录或无权限时安装器会明确停止。Private 拉取只走 GitHub 官方地址，不经过公共镜像，也不以公开 ZIP 兜底。

**WorkBuddy 侧：** `docs/workbuddy-install-and-guide.md` + `docs/workbuddy-system-prompt.md`  
**刷新业务包（制作）：** `python3 scripts/refresh_business_delivery.py`

---

## 分工（一句话）

| 角色 | 做什么 | 不做什么 |
|------|--------|----------|
| **业务** | 在 WorkBuddy 说安装句；在引导下预览选模板、填 Word、交授权图、审初稿、点确认、收成片 | 自己解压 zip、装 Node、起端口、调 TTS、改坐标/图层；**自己找图标站或交网图当正式符号** |
| **WorkBuddy** | clone/更新仓库、打开引导页、逐步指引、锁定模板、解析 Word、内容驱动、列缺口、确认后出 PPTX/MP4；缺小图标时按需从 Koboyo 匹配（本机临时，见 `SOURCE.md`） | 把正常 settled 单甩回「请找制作」；编造医学结论；假包装；系统机器人音色；整库镜像/提交图标包 |

---

## 端到端（双方一起完成交付）

```text
业务                              WorkBuddy
────                              ────────
① 打开 WorkBuddy，粘贴安装句  →
                                  ② 安装 Public 入口 → 授权检查
                                  ③ 拉取 Private → bootstrap
                                  ④ 打开 index.html，开始四步指引
⑤ 预览选模板
⑥ 填空白 Word + 授权图
⑦ 附件或上传区提交            →
                                  ⑧ 锁定 template / style_pack / voice
                                  ⑨ 解析内容（N 条→N 行）
                                  ⑩ 交「内容初稿 + 缺口」或「分镜 + 缺口」
⑪ 审阅、改文案、确认          →
                                  ⑫ 生成终稿 PPTX 和/或 MP4
⑬ 成片归档 / 门店使用
```

业务**不需要**自己点生成器、也**不需要**解压包；**需要** WorkBuddy 把安装与 ⑧～⑫ 做完。

---

## 业务侧操作（你 · 一句话启动）

1. 打开 **WorkBuddy**  
2. 输入：

```text
请安装 https://github.com/lmr1123/chain-pharmacy-content-studio.git，然后指引我使用
```

3. **三步做完：**  
   1）看模板（引导页预览 + 选用）  
   2）输入培训内容，例如：  
   `整理可可康灵芝胶囊商品，主要是围绕宁心安神助睡眠、提升免疫力、保肝护肝抗衰老3个方面来完善，你先整理符合内容再生成ppt`  
   3）可下载 PPT 修改，或输入指令批量修改，例如「第二页卖点改成…」「批量把联合用药改成 2 条」

### 数字人侧讲模式（可选）

业务包：`outputs/业务使用资料包/药店培训内容工厂-业务包/08_数字人侧讲模式/`  
技术入口：`docs/digital-human-presenter-mode.md`

1. 说「这个课件用数字人模式」  
2. WorkBuddy **先**交：全课旁白脚本 + **数字人页清单（页码写清）**  
3. 业务确认「可以生成」后，才生成数字人（确认前不调 HeyGen、不产生数字人费用）  
4. 非关键页：全宽课件 + 同声旁白、不站静帧人；全课同一药师克隆声  

---

## WorkBuddy 侧必须做到（代理）

1. 识别安装句 → 克隆 Public installer，运行 `scripts/install_private_studio.py`；授权安装完成后，才运行 Private 内的 `scripts/workbuddy_bootstrap_for_business.py`
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

如确需离线分发，只能由管理员通过受控渠道交付获授权版本，并记录接收人、版本与哈希；不得把业务包 ZIP 放入 Public、群聊或公开网盘。
**正式交付仍走默认安装句和 Private 授权**，Public 不提供生产 ZIP 备用路径。

---

## 和「一键无人值守」的区别

- **我们做的：** 业务一句话 → WorkBuddy 安装并引导 → 对话协作高质量交付。  
- **我们没承诺的：** 业务电脑上没有任何代理、只双击 Word 就出片。
