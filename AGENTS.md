# Project-specific production rule

**进度（2026-08-09 业务验收修正）：** 自然语言推荐是业务主入口；绿色 5 页、疾病-商品-场景 18 页、课件3 13 页和成分健康科普 20 页均为一等高保真路线，构件化 PPT 只在未匹配固定课型时作灵活兜底，绝不是直接套福尔 16 页。此前“绿色五页下线”的状态已由本次验收决策取代；速福达课件3 MP4 仍未上线。
**当前专项（2026-08-10）：** WorkBuddy 真实业务验收；业务路线与能力状态以机器真值为准，历史交接仅作背景。
**业务怎么用 / 测试案例：** `docs/business-usage-and-test-cases.md`

## Locked direction (do not drift)

Primary deliverable: complete, high-quality training **video/courseware** with unified style and clear structure—not an element stockpile.

Order: gold-sample full replica → lock framework + `style_pack` → extend themes in that style.  
Do not treat generic asset pre-stocking as main progress.

Canonical records (no separate policy doc):

- decision: `decision.gold-sample-first` → `python3 scripts/query_production_library.py --type decision --text 金样`
- lesson: `lesson.gold-sample-not-asset-stockpile` / `tasks/lessons.md`
- brief: `docs/project-brief.md` §推进原则

If a plan conflicts with the above, stop and realign.

## For any production task

1. Follow `skills/pharmacy-template-replication/SKILL.md` and the locked decision above.
2. Query `production-library/catalog.json` via `scripts/query_production_library.py` before creating style/component/effect/voice/image/template.
3. One `style_pack_id` per project.
4. Prefer gold-sample quality or same-framework theme extension; assets only for declared framework slots.
5. Register approved additions; record corrections in `tasks/lessons.md` + registries.
6. Business provides packshots/logos/evidence; never fake brand packaging.
7. Store each user-confirmed template in its own
   `production-library/templates/settled/<template-slug>/` directory with one canonical
   artifact, `业务提交_空白模板.docx`, `业务提交_填写参考.docx`, and manifest. Keep the
   authoritative Word sources in the manifest and refresh directory copies through
   `scripts/sync_settled_template_business_words.py`. Store all exploratory renders, rejected
   variants, comparisons, and QA only under `production-library/validation/`; never mix them
   in a shared `out` or `output` directory.
8. **UI / layout / small object icons (on demand):** when a gold-sample slot needs
   arrows, bullets, checks, dividers, or simple medical object marks and nothing
   approved exists in `component-library`, match and fetch from
   [Koboyo Icons](https://koboyo.com/icons) into local
   `assets/_intake/open_source/koboyo/svg/` (gitignored; see `SOURCE.md` +
   `license.txt`). Do **not** commit bulk SVG or mirror the full library. Do **not**
   replace multi-color scene illustrations (symptoms, advice scenes, presenters).
   Digits 1–n prefer text typesetting. Promote to master only after recolor/rasterize
   and sign-off.

## Business + WorkBuddy self-serve (no unzip, no maker-for-normal)

Business opens WorkBuddy and says:

```text
请安装 https://github.com/lmr1123/chain-pharmacy-content-studio-private.git，然后指引我使用
```

**Single production repository.** WorkBuddy clones that URL (official HTTPS, shallow clone)
into `~/Documents/chain-pharmacy-content-studio-private` and runs
`scripts/workbuddy_bootstrap_for_business.py`. Business needs **no** GitHub account.
Never ask business to use GitHub, SSH, tokens, or a CLI. Never use public mirrors.
If the business still pastes the old installer URL (`chain-pharmacy-content-studio` without
`-private`), run its `scripts/install_private_studio.py` once (forwarder) or redirect them to
the production URL above.

**Locked model:** business provides content in chat; **WorkBuddy on the business machine**
produces PPT / product video / health video. Do **not** bounce normal settled work to
「请找制作」or require the engineer to run renders.

After installation, agent must: `git pull --ff-only` in this checkout +
`scripts/workbuddy_bootstrap_for_business.py`, open the portal,
then on content: recommend route → explain and confirm courseware → organize → **run generators**.
Before render: `python3 scripts/probe_production_env.py` (honest degrade if no TTS/ffmpeg).

**Unified production path (P1 control plane + P2 runtime profiles):** the business starts either
from the portal action「我不懂模板，帮我选」or by stating the desired deliverable and available
materials. WorkBuddy must run the recommender first; do not ask business to choose a route ID.
Prefer the unified job
runner for wired self-serve routes instead of asking business to paste internal
generator flags:

```bash
python3 scripts/business_job.py recommend --text '<自然语言需求>' --check-env
# 固定课型：业务确认推荐课型后，可继续沿用 notes/Word 整理草稿
python3 scripts/business_job.py new --route <confirmed-fixed-route> --theme <主题> --notes '...' --auto-draft
# 构件兜底：先给业务确认中文页签大纲、来源解释和单一视觉，再由 WorkBuddy 内部锁定脚本
python3 scripts/business_job.py new --route product-pptx-component-v1 --theme <主题> --script-json <WorkBuddy内部确认版脚本.json> --auto-draft
# 按 route 完成全部闸门；若命中构件兜底，顺序固定如下
python3 scripts/business_job.py approve --job <id> --gate content --by <姓名>
python3 scripts/business_job.py approve --job <id> --gate visual --by <姓名> --asset-bindings <bindings.json>
python3 scripts/business_job.py approve --job <id> --gate product_image --by <姓名> --product-image <授权包装图> --authorization-reference <凭证>
python3 scripts/business_job.py render --job <id>
python3 scripts/business_job.py status --job <id>
python3 scripts/business_job.py open --job <id>
```

构件路线的 notes-only 入口只生成“待确认中文页签大纲”草稿，绝不能作为正式锁定编排；业务确认大纲、来源解释和单一视觉后，由 WorkBuddy 内部生成确认版 script-json，再创建统一任务。Business never edits JSON or page-type IDs，也不接触 route、页型或视觉包的内部 ID。

- Routes truth: `production-library/business-routes.json`（`default_pptx_route` = component 是技术兜底指针，不代表覆盖固定课型推荐）
- Selection/capability map: `production-library/business-route-selector.json`（只存业务意图、金样 lineage 与可复用能力；不得复制 active/gates/env 真值）
- Runtime profiles: `production-library/runtime-profiles.json`（pptx / video-full / optional-external）
- **Generic fallback PPT engine:** `production-library/engines/courseware-pptx-v1/` + `scripts/generate_courseware.py`（构件 + recipe；动态页数，不是福尔 16 页复刻器）
- Green fixed-courseware engine: `production-library/engines/product-courseware-green-v1/`
- Disease-product-scenario fixed-courseware engine: `production-library/engines/disease-product-scenario-pptx-v1/`
- Courseware3 fixed PPT engine: `production-library/engines/courseware3-pptx-v1/`
- Video full runtime: `production-library/engines/video-revideo-runtime-v1/`（`kit` 可 symlink 历史 `poc/gold-sample`；业务代码经 `scripts/video_runtime.py` 解析）
- 商品正式视频环境：`python3 scripts/video_full_env.py check|soft-repair|package|restore`（说明 `docs/video-full-env-package.md`）
- Active PPT now: `product-pptx-green-v1`（金银花绿色 5 页）、`product-pptx-disease-scenario-v1`（穿心莲 18 页）、`courseware3-pptx-v1`（速福达课件3 13 页）、`ingredient-health-edu-pptx-v1`（成分健康科普 20 页）为一等固定路线；`product-pptx-component-v1` 为未匹配固定结构时的动态兜底
- Active ingredient-health PPT: `ingredient-health-edu-pptx-v1` / `template.kangaisen-lycopene-health-edu-v1`（番茄红素成分健康科普 PPT，米白番茄红，20 页）可自助生成，须走 content + visual（`product_image=false`），并显式绑定 69 个本主题新图。这是成分健康科普课型，**不是**福尔课件4；业务提供已审核医学/健康口径与可授权图片，严禁继承康爱森/番茄红素金样文案或原图。
- Active product video: `product-mp4-full-v1`（另需 `approve --gate product_image`）
- Not active: `courseware3-mp4-v1`（速福达课件3 MP4；不得向业务承诺或用 PPT 成功代替视频成功）
- Job workspace (gitignored): `outputs/workbuddy-workspaces/jobs/`
- Pickup: `outputs/业务使用资料包/药店培训内容工厂-业务包/05_交付物放这里/<job_id>/`
- Pending approval / env block / QA fail never publish into the delivery folder
- New-theme drafts must not leak gold medical/price/combo copy; residual tokens hard-block draft

Legacy direct generators remain for maker debugging and not-yet-wired templates; normal business work uses `business_job.py`:
- PPT 构件生成器：`scripts/generate_courseware.py`；绿色五页引擎：`product-courseware-green-v1`
- 课件3旧直连：`scripts/generate_business_courseware.py --template courseware3 --theme <dir>`（仅制作侧调试；业务固定 PPT 走 `courseware3-pptx-v1`）
- 视频：`generate_business_video.py --mode full`（product 8 / health 7 segments）；never default `audio-shell`。
  商品 full 必须带业务授权包装图，并以 `product-video-approval-v1` 绑定 8 段审核稿、
  包装图 SHA-256、批准人、时间和授权凭证；健康 full 必须先用 `build_health_theme_package.py`
  生成主题包、补齐内容/画面并完成 SHA-256 绑定审批，再以 `--theme-package` 出片；
  正式渲染/交付禁止 `--skip-visual-approval`。
Always write `voice_id` from template manifest; never system TTS for formal narration.
See `docs/workbuddy-install-and-guide.md`, `docs/workbuddy-system-prompt.md`,
`docs/workbuddy-video-first-check.md`. Do **not** tell business to unzip zip as default.

### Digital-human presenter mode (scheme C)

When business says 数字人模式 / 真人数字人侧讲 / 方案 C:

1. This is a **manual SOP / conditional production mode**, not an automatic local self-serve route.
2. **Do not** call HeyGen or clone the final narration track until business separately confirms
   the final script **and** the key-page list (which pages get the digital human).
3. Deliver a review pack first: full narration scripts + key pages table (page / section / why).
4. Production prerequisites: available HeyGen key/quota, a confirmed editable courseware file,
   authorized portrait material, and local Qwen TTS + rembg + ffmpeg.
5. After both confirmations and explicit「可以生成」: same voice pack for all pages; only key pages get DH;
   non-key = full-width slide + narration, no static avatar.
6. Entry: `docs/digital-human-presenter-mode.md`
   Business pack: `outputs/业务使用资料包/药店培训内容工厂-业务包/08_数字人侧讲模式/`

### Seedance health-edu video mode (prompt-only)

When business says Seedance 科普 / 生活避险科普 / 扁平头部五拍 / 元提示词生活科普
（若只说「健康科普视频」且未指明，先问：九宫格林医生线 or Seedance 生活避险线）:

1. **Not** the internal 疾病科普视频 Remotion line (`health-video-reference-tech-v1`).
2. Expand theme via meta-prompt variables → deliver **《科普脚本复核包》** first.
3. After explicit「脚本通过 / 可以出 Seedance 提示词」: write segmented Seedance 2.0 prompts
   (≤15s each) + 视频号 publish pack (title / disclaimer / forward text).
4. WorkBuddy local deliverable = **review pack + copy-paste prompt/publish pack only**.
   The final video is generated on Seedance / 即梦 with the business's external account;
   do not describe the local scaffold as a finished video or call paid APIs without explicit cost approval.
5. Compliance: no white coat, no medical devices, no pathology jargon — lifestyle /
   environment safety / emotion regulation only; always include disclaimer.
6. Entry: `docs/seedance-health-edu-video-mode.md`  
   Meta-prompt: `production-library/templates/prompt-modes/seedance-health-edu-v1/`  
   Review: `python3 scripts/scaffold_seedance_health_edu.py --vars <json>`；
   approved release: 同一命令追加 `--release --approval <approval.json>`。
   Business pack: `outputs/业务使用资料包/药店培训内容工厂-业务包/09_健康科普Seedance模式/`

### Jiugongge health-edu — two parallel modes

| 业务说法 | 模式 ID | 角色 | 医疗元素 |
|----------|---------|------|----------|
| 九宫格原版 / 林医生王大爷 | `jiugongge-health-edu-v1` | 林医生+王大爷 | 卡通诊室/白大褂允许 |
| 九宫格合规版 / 无医疗 | `jiugongge-health-edu-compliance-v1` | 小林+受众 | **严禁**医生医院器材病名话术 |

**A. 原版** (`docs/jiugongge-health-edu-video-mode.md`)

1. Theme + 1–3 knowledge points → 六段口播复核 → 确认后三视图+六段提示词+发布包  
2. Review: `python3 scripts/scaffold_jiugongge_health_edu.py --vars <json>`；确认后追加
   `--release --approval <approval.json>`
3. Assets: `production-library/templates/prompt-modes/jiugongge-health-edu-v1/`  
4. Business: `10_健康科普九宫格模式/`

**B. 合规版无医疗** (`docs/jiugongge-health-edu-compliance-mode.md`)

1. Theme + audience + habit points → 脱敏+口播复核 → 确认后资产+英九宫格/视频+发布全家桶  
2. 红线 0 命中：医生/白大褂/医院/诊室/器材/预防治疗缓解/病名  
3. Review: `python3 scripts/scaffold_jiugongge_health_edu_compliance.py --vars <json>`；确认后追加
   `--release --approval <approval.json>`
4. Assets: `production-library/templates/prompt-modes/jiugongge-health-edu-compliance-v1/`  
5. Business: `11_健康科普九宫格合规版/`

Both: not Seedance 五拍；not disease Remotion MG；WorkBuddy locally creates the review,
character/scene prompts, six-segment prompt pack, and publish pack only. Final images/video are
generated on the selected external image/video platform with the business's account.

## Product PPT courseware: route selection + business workflow

1. Run `business_job.py recommend --text '<自然语言需求>'` internally, or accept the portal
   action「我不懂模板，帮我选」. Return one recommendation; if ambiguous, return exactly two
   candidates and one business question. Do not create a job before the business confirms.
2. Fixed 5 / 18 / 13 / 20-page courseware are first-class high-fidelity routes. A matching fixed
   route wins; the component route is only the flexible fallback when none matches. The component
   route does not mean copying the 16-page 福尔 courseware.
3. For the flexible component route, business provides only the delivery goal and approved content.
   WorkBuddy first proposes a Chinese tab outline, source explanation, and one visual style without
   locking a job. After business confirmation, WorkBuddy writes the confirmed script-json and its
   internal `page_sequence`, then creates the unified job. Notes-only component intake remains an
   outline-only pending draft and cannot become the formal locked composition. Business never edits
   JSON or page-type IDs. Reusable contracts currently include the green courseware's 商品信息总览, the
   disease-scenario courseware's 门店咨询框架, and courseware3's 商品证据阶梯; registered new page
   types may be added when the content requires them. Every resulting deck locks exactly one
   `style_pack_id`; source courseware contributes structure, not mixed masters, source copy, or images.

When extending an active courseware route:

1. Accept **partial materials** (even product name only).
2. Produce a **content draft + gap list** for business approval (do not skip to final PPT or invent medical copy).
3. Business provides authorized packshots / logos / evidence; WorkBuddy generates and binds only
   the declared non-product illustration slots and previews a representative in-slot result.
4. For the component route, approvals are ordered **content → visual (`asset-bindings`) →
   product_image**. The product image must be a business-authorized original; generated illustrations
   cannot substitute for it. Fixed product routes follow their route gates; the 20-page ingredient
   courseware uses content + visual and has no product-image gate.
5. Generate the formal **PPTX**, run per-slide QA, and publish only after QA passes.

Business talks only to WorkBuddy in Chinese. WorkBuddy owns internal JSON, CLI, image bindings,
approval records, and QA; never ask business to edit them directly. Courseware3 formal self-serve
delivery is PPTX only until `courseware3-mp4-v1` is explicitly activated.

Current multi-source component evidence lives at
`production-library/validation/courseware/multi-gold-composition-uat-v1/`: A / B / C r4 deliver 7 /
6 / 5 distinct pages through all three `business_job` gates. **r4 逐页已通过**：artifact-tool
18 / 18, all fixture business copy is present in PPT, gold terms / source-image SHA / placeholders
are zero, all three Presentations `slides_test` runs report no overflow, and manual per-slide review
is complete（人工逐页复核完成）. This is UAT courseware evidence, not permission to expose unfinished portal state.
The suite v3 hash-bound gate has passed and the A / B / C preview suite is now synced into the
business portal. Future rebuilds must remain fail-closed: if the bound deck/page/review hashes or
visual checks stop matching, hide the suite instead of falling back to an old gold-sample preview.

Canonical workflow (Chinese, for business + agent):  
`production-library/templates/settled/product-courseware-green-v1/业务使用流程.md`
