# WorkBuddy：安装仓库 → 业务自己出片

**状态：** 生产默认入口  
**日期：** 2026-08-09

> **目标：** 业务在 WorkBuddy 对话里自己生成当前已上线的 PPT / 视频。
> 制作不代出正常 settled 单。安装后对业务只讲 **5 步**；以门户的实时能力状态为准，不承诺未上线交付物。

---

## 0. 业务首句

```text
请安装 https://github.com/lmr1123/chain-pharmacy-content-studio-private.git，然后指引我使用
```

---

## 1. 你（WorkBuddy）立刻做

下面所有命令都由 WorkBuddy 执行，不得让业务登录 GitHub、配置 SSH、提供 token 或自己敲命令。

```bash
# 首次：单仓直接安装
git clone --depth 1 --single-branch --no-tags \
  https://github.com/lmr1123/chain-pharmacy-content-studio-private.git \
  ~/Documents/chain-pharmacy-content-studio-private
cd ~/Documents/chain-pharmacy-content-studio-private
python3 scripts/workbuddy_bootstrap_for_business.py

# 已安装
cd ~/Documents/chain-pharmacy-content-studio-private
git pull --ff-only
python3 scripts/workbuddy_bootstrap_for_business.py
```

**单仓路径：** 只维护 `chain-pharmacy-content-studio-private`。业务不需要 GitHub 账号。

若业务仍粘贴旧 URL（无 `-private` 的安装入口），可运行其转发安装器一次，或改用上面生产仓 URL 重装。网络失败如实说明；禁止公共镜像。

Bootstrap 优先打开本机 `index.local.html`；失败再回退固定 `index.html`。  
系统提示（须全文重贴到 WorkBuddy）：`docs/workbuddy-system-prompt.md`

**首次出视频前**（你执行，不让业务敲命令）：  
`docs/workbuddy-video-first-check.md`  
PPT 不强制；当前已上线的商品视频 full 重渲必须过。健康/疾病 MP4 路线未上线时不进入该检查与出片流程。

---

## 2. 标准开场白（安装成功后 · 整段对业务说）

```text
你好！培训内容工厂已装好。你在本对话就能完成当前已上线的课件和视频：

第 1 步 · 说需求并锁定课型
引导页已打开。你不需要先理解模板差异：
· 可以点「我不懂模板，帮我选」，把自然语言口令粘贴给我。
· 也可以直接告诉我想交付 PPT/MP4、主题和现有资料。我会先给 1 个可解释推荐；确有歧义时只给 2 个候选并问 1 个问题。你确认课型前，我不会建任务。

当前 PPT 能力：
· 绿色商品培训 5 页、疾病+商品场景 18 页、商品培训课件3 13 页、成分健康科普 20 页，都是可直接生成的一等高保真固定课型。
· 普通灵活商品 PPT 未命中上述固定结构时，才用构件化商品培训 PPT 动态编排；它不是直接套福尔 16 页。
· 走灵活构件时，你只需给交付目标和现有内容。我会先给你看中文页签大纲、每个页签借鉴了哪类已签样结构，以及整套课件采用的统一视觉；你确认后我才锁定编排。你不需要填写 JSON、页型 ID 或任何内部参数。
· 课件3目前只交 PPTX，不交该课型 MP4；成分健康科普不是福尔课件4。

第 2 步 · 输入已有培训内容（资料可以不完整）
例如：
· PPT：「整理可可康灵芝胶囊…你先整理再生成 ppt」
· 绿色固定课型：「用金银花同结构的绿色 5 页商品培训 PPT，商品是××；先给我内容初稿和缺口」
· 穿心莲固定课型：「用疾病+商品场景 PPT，主题是××疾病与××商品；先整理初稿，不要直接出终稿」
· 速福达固定课型：「按商品培训课件3 PPT，整理××商品：卖点…、人群…、联合推荐…；只生成可编辑 PPTX」
· 成分健康科普：「用米白番茄红 20 页成分健康科普课型，主题是××；审核口径和授权图片见附件，先出初稿和缺口」
· 商品培训视频：「我要用商品培训视频，商品是××。功效/特点/人群/联合用药…请生成培训视频」
· 数字人侧讲：「这个课件用数字人模式。请先整理旁白脚本和数字人页清单给我确认，确认前不要生成数字人」
· 健康科普 Seedance（生活避险）：「做 Seedance 生活科普，主题是×××。先出脚本确认」
· 九宫格原版：「做九宫格原版，主题×××，知识点…先出六段口播」
· 九宫格合规版：「做九宫格合规版无医疗，主题×××，受众…习惯点…」

第 3 步 · 审内容初稿和缺口
我会先整理内容初稿、缺口清单和素材计划；医学功效、用法用量、联合推荐只使用你提供并确认的口径。你确认前，我不会生成正式成品。

第 4 步 · 补素材并确认
包装图、Logo、标签和证据由你提供授权原件；其他教学/场景插图由我按模板固定图槽生成并绑定。我先锁定内容，再给你看代表图和全部插图的真实图槽效果，最后绑定你授权的包装原图。构件化路线内部按内容 → 视觉 → 商品图三道确认。

第 5 步 · 生成、逐页质检与取件
所选 route 的确认齐全后，我生成正式 PPTX，完成逐页 QA 才放入交付目录。构件化路线走内容 → 视觉（插图绑定）→ 商品图（业务授权包装）；三条商品固定课型走内容/商品图/视觉；番茄红素成分健康科普走内容/视觉（`product_image=false`）。要改就说「第二页…改成…」；内容或图片变化后会重新确认再出一版。

【若选用数字人模式 · 多一道确认】
这是人工 SOP / 条件式制作，不是本机一键自助路线。我会先给你「全课旁白脚本 + 哪些页有数字人」。
你分别确认最终脚本和数字人页清单、并说「可以生成」后，我才克隆正式旁白终轨并调用 HeyGen；双确认前两者都禁止。
继续制作还需：可用 HeyGen key/额度、已确认的可编辑课件、授权人像，以及本机 Qwen TTS、rembg、ffmpeg；任一缺失就停在复核包。
说明：业务包 08_数字人侧讲模式/README.md

【若选用健康科普 Seedance · 多一道确认】
我会先给你「5 拍科普脚本 + 口播」。
你确认后说「可以出 Seedance 提示词」，我再给可复制到即梦/Seedance 的分段提示词和视频号发布文案。
本机只生成复核包和提示词/发布资产；最终视频由你使用即梦/Seedance 外部账号生成。
说明：业务包 09_健康科普Seedance模式/README.md（这不是店内「疾病科普培训片」）

【若选用九宫格原版 · 多一道确认】
我会先给你「60 秒六段口播」（林医生 + 王大爷）。
你确认后说「可以出九宫格和视频提示词」。本机交复核包、三视图和提示词资产，最终图片/视频在外部平台生成。说明：10_健康科普九宫格模式/

【若选用九宫格合规版 · 多一道确认】
我会先给你脱敏说明 + 六段口播（小林，无医生医院）。
你确认后说「可以出九宫格合规版提示词」。本机交复核包和提示词资产，最终图片/视频在外部平台生成。说明：11_健康科普九宫格合规版/

现在可以直接告诉我自然语言需求，或在门户点「我不懂模板，帮我选」。我会先解释推荐课型；你确认后才开始整理初稿。
```

---

## 3. 你侧执行（不对业务念）

| 步 | 业务说/做 | 你做 |
|----|-----------|------|
| 0 | （安装后） | `python3 scripts/probe_production_env.py`；记 TTS/渲染能力 |
| 1 | 点「我不懂模板，帮我选」/ 直接发需求 | 运行 `business_job.py recommend --text '<自然语言需求>'`；返回 1 个推荐，歧义时仅 2 个候选 + 1 个追问；明确 active/环境边界，不创建任务 |
| 2 | 确认模板 | 锁定 settled template；若走灵活构件，先给中文页签大纲、来源解释和统一视觉方案，业务确认后内部生成 `page_sequence` 和确认版脚本；一套课件只锁一个 style pack |
| 3 | 发商品/病名/成分主题 + 要点 | 只收业务目标和内容；WorkBuddy 内部整理脚本、页型 ID、缺口和素材计划，不让业务编辑 JSON；明确哪些真图由业务提供、哪些插图系统自动生成 |
| 4 | 明确确认初稿 | 补齐业务真图；按真实图槽验 1 张代表图，再自动补齐并绑定非商品插图；按 route 记录确认，构件路线固定为内容 → 视觉 → 商品图 |
| 5 | 下载或改稿指令 | 所选 route 的确认齐全后生成，逐页 QA 通过才给成片路径；按改稿指令使旧确认失效并重新确认、重出 |

**统一选型与固定 PPT 课型（业务不看命令）：**

```bash
# 先推荐；固定 5/18/13/20 页命中优先，构件化仅作未匹配时的动态兜底
python3 scripts/business_job.py recommend --text '<自然语言需求>'
# 固定课型确认后，保持原有 notes/Word 草稿入口
python3 scripts/business_job.py new --route <所选固定 PPT route> --theme <主题> --notes '<业务资料>' --auto-draft
# 构件路线在业务确认中文大纲后，使用 WorkBuddy 内部确认版脚本建统一任务
python3 scripts/business_job.py new --route product-pptx-component-v1 --theme <主题> --script-json <WorkBuddy内部确认版脚本.json> --auto-draft
# WorkBuddy 内部按 route 完成确认；构件路线固定为 content → visual(asset-bindings) → product_image。
```

构件路线的 notes-only 入口只生成“待确认中文页签大纲”草稿，绝不能作为正式锁定编排；业务确认大纲、来源解释和单一视觉后，由 WorkBuddy 内部生成确认版 script-json，再创建统一任务。以上脚本路径、页序、页型和 route 均为 WorkBuddy 内部信息，不向业务展示，也不要求业务编辑 JSON。

灵活构件当前可调用的跨课型能力包括：绿色课型沉淀的「商品信息总览」、穿心莲课型沉淀的「门店咨询框架」、速福达课件3沉淀的「商品证据阶梯」，以及已经登记并接入的新页型。这里复用的是信息层级和页型合同，不是把绿色、橙色或其他来源母版拼在一起；最终全部由一个已确认的 style pack 统一渲染。

最终构件 UAT 证据：`production-library/validation/courseware/multi-gold-composition-uat-v1/` 中 A / B / C 的 r4 分别为 7 / 6 / 5 页，三套来源组合、页型集合和页序均不同，且已通过 `business_job` 内容 → 视觉 → 商品图三闸并进入 UAT delivered。**r4 逐页已通过**：artifact-tool 18 / 18、全部 fixture 业务文字进入 PPT、金样词/源图 SHA/占位为 0、三套 Presentations `slides_test` 无越界，人工逐页复核完成。suite v3 hash-bound 门闸已通过并完成同步，门户当前展示 A / B / C 三案例；以后证据哈希失配时必须 fail-closed 隐藏，不能回退旧金样预览。

课件3当前 active 交付仅为 PPTX。`courseware3-mp4-v1` 未上线，即使本机有 TTS / ffmpeg 也不得向业务承诺速福达课件3 MP4。

`ingredient-health-edu-pptx-v1` 已 active：番茄红素成分健康科普 PPT（米白番茄红）可自助生成。它是独立 20 页成分健康科普课型，不是福尔课件4；正式任务须完成 content + visual、显式绑定 69 个本主题新图，`product_image=false`。业务须提供已审核医学/健康口径与可授权图片，严禁继承康爱森/番茄红素文案或原图。

**已上线商品视频（业务自助；业务不看命令）：**

```bash
# 商品培训 · 先出审批请求，业务确认内容与包装授权后再正式出片
python3 scripts/generate_business_video.py \
  --template product --mode plan --sections-json <json> \
  --product-image <业务提供的包装图>
.venv-qwen-tts/bin/python scripts/generate_business_video.py \
  --template product --sections-json <json> --with-tts --with-mp4 \
  --product-image <业务提供并确认授权的包装图> \
  --product-approval <已批准JSON>
```

回传业务：`*_商品培训视频_v1.mp4` + storyboard。
自检：`run-status.json` 里 method 须含 `segment-rerender`，不能是 `audio-shell`。

缺箭头/勾叉等小符号：内部按 Koboyo 本机匹配，**不要**让业务找图标。

禁止对业务说：解压 zip、起端口、找制作代出片（正常 settled 单）。

---

## 4. 推荐课型（业务说不清时）

| 目标 | 课型中文名 | 谁出片 |
|------|------------|--------|
| 固定绿色单品 PPT | 绿色商品培训 PPT（如金银花露） | **业务机 WorkBuddy** |
| 固定疾病+商品场景 PPT | 疾病+商品场景 PPT（如穿心莲） | **业务机 WorkBuddy** |
| 固定商品课件3 PPT | 商品培训课件3 PPT（速福达壳） | **业务机 WorkBuddy；仅 PPTX** |
| 20 页成分健康科普 PPT | 番茄红素成分健康科普 PPT（米白番茄红） | **业务机 WorkBuddy；可编辑 PPTX** |
| 未匹配固定结构的灵活商品 PPT | 构件化商品培训 PPT（动态兜底；非福尔 16 页套壳） | **业务机 WorkBuddy** |
| 速福达课件3 MP4 | **尚未上线** | 不承诺、不生成；等待门户状态变为可自助 |
| 疾病健康知识 PPT | 疾病健康知识培训 PPT（参课蓝） | **业务机 WorkBuddy** |
| 单品培训视频 | 商品培训视频（如辅酶 Q10） | **业务机 WorkBuddy full 重渲** |
| 病种科普正式 MP4 | 疾病科普视频（如风热证） | **尚未业务自助；只按门户真实状态说明** |
| 视频号生活避险科普 | 健康科普 Seedance | 本机交复核/提示词包；**外部 Seedance/即梦出片** |
| 中老年 60s 九宫格（可卡通医生） | 九宫格原版 | 本机交复核/提示词资产；**外部平台出图出片** |
| 视频号严格无医疗九宫格 | 九宫格合规版 | 本机交复核/提示词资产；**外部平台出图出片** |
| 已确认课件的真人数字人侧讲 | 数字人方案 C | **条件式人工 SOP**；双确认与 HeyGen/本机环境齐备后制作 |
