# Project-specific production rule

**进度（2026-08-09 收工）：** P0–P2 已合 Private `main`（默认构件 PPT、绿色五页下线、`video_full_env`）。  
**明日专项：** 业务验 PPT · 健康视频自助 — 见 `docs/session-handover-2026-08-09.md` 与 `tasks/todo.md` 顶部快照。  
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
请安装 https://github.com/lmr1123/chain-pharmacy-content-studio.git，然后指引我使用
```

The URL above is the **sanitized Public installer**, not the production repository.
It contains no settled templates, previews, voices, assets, business package, or generation
capability. WorkBuddy must run `scripts/install_private_studio.py`, use the user's existing
GitHub credential manager/session to verify `read` access to
`lmr1123/chain-pharmacy-content-studio-private`, then clone/update that Private repository
and run its bootstrap. Never put a token in a URL or log; never send the Private clone
through a public mirror; never fall back to a public ZIP. If the user is not logged in or
not authorized, stop with the exact access gap instead of pretending the factory is installed.

**Locked model:** business provides content in chat; **WorkBuddy on the business machine**
produces PPT / product video / health video. Do **not** bounce normal settled work to
「请找制作」or require the engineer to run renders.

After authorized Private installation, agent must: `git pull --ff-only` in the Private
checkout + `scripts/workbuddy_bootstrap_for_business.py`, open the portal,
then on content: lock template → organize → **run generators**.
Before render: `python3 scripts/probe_production_env.py` (honest degrade if no TTS/ffmpeg).

**Default production path (P1 control plane + P2 runtime profiles):** prefer the unified job
runner for the two wired self-serve routes instead of asking business to paste internal
generator flags:

```bash
python3 scripts/business_doctor.py --route product-pptx-component-v1   # honest env + install hints
python3 scripts/workbuddy_bootstrap_for_business.py --route product-pptx-component-v1 --no-open
# 或 --profile pptx / video-full；默认只强制 production-assets，加 route 才硬校验对应能力
python3 scripts/business_job.py list-routes
python3 scripts/business_job.py new --route product-pptx-component-v1 --theme <商品名> --notes '...' --auto-draft
# 完整审核脚本：再加 --script-json path/to/script.structured.json
python3 scripts/business_job.py approve --job <id> --gate content --by <姓名>
python3 scripts/business_job.py render --job <id>
python3 scripts/business_job.py status --job <id>
python3 scripts/business_job.py open --job <id>
```

- Routes truth: `production-library/business-routes.json`（`default_pptx_route` = component）
- Runtime profiles: `production-library/runtime-profiles.json`（pptx / video-full / optional-external）
- **Default PPT engine:** `production-library/engines/courseware-pptx-v1/` + `scripts/generate_courseware.py`（构件 + recipe）
- Green PPT engine (retired route): `production-library/engines/product-courseware-green-v1/`（仅调试 `--force`）
- Video full runtime: `production-library/engines/video-revideo-runtime-v1/`（`kit` 可 symlink 历史 `poc/gold-sample`；业务代码经 `scripts/video_runtime.py` 解析）
- 商品正式视频环境：`python3 scripts/video_full_env.py check|soft-repair|package|restore`（说明 `docs/video-full-env-package.md`）
- Active now: `product-pptx-component-v1`（默认 PPT）、`product-mp4-full-v1`（商品 full MP4；另需 `approve --gate product_image`）
- Retired: `product-pptx-green-v1`（绿色五页壳；代码保留可回滚，业务自助已关闭）
- Job workspace (gitignored): `outputs/workbuddy-workspaces/jobs/`
- Pickup: `outputs/业务使用资料包/药店培训内容工厂-业务包/05_交付物放这里/<job_id>/`
- Pending approval / env block / QA fail never publish into the delivery folder
- New-theme drafts must not leak gold medical/price/combo copy; residual tokens hard-block draft

Legacy direct generators remain for maker debugging and not-yet-wired templates:
- PPT 构件生成器：`scripts/generate_courseware.py`；绿色五页兼容：`product-courseware-green-v1`
- 课件3：`scripts/generate_business_courseware.py --template courseware3 --theme <dir>`  
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

1. **Do not** call HeyGen until business confirms the final script **and** the key-page list
   (which pages get the digital human).
2. Deliver a review pack first: full narration scripts + key pages table (page / section / why).
3. After explicit「可以生成」: same voice pack for all pages; only key pages get DH;
   non-key = full-width slide + narration, no static avatar.
4. Entry: `docs/digital-human-presenter-mode.md`  
   Business pack: `outputs/业务使用资料包/药店培训内容工厂-业务包/08_数字人侧讲模式/`

### Seedance health-edu video mode (prompt-only)

When business says Seedance 科普 / 生活避险科普 / 扁平头部五拍 / 元提示词生活科普
（若只说「健康科普视频」且未指明，先问：九宫格林医生线 or Seedance 生活避险线）:

1. **Not** the internal 疾病科普视频 Remotion line (`health-video-reference-tech-v1`).
2. Expand theme via meta-prompt variables → deliver **《科普脚本复核包》** first.
3. After explicit「脚本通过 / 可以出 Seedance 提示词」: write segmented Seedance 2.0 prompts
   (≤15s each) + 视频号 publish pack (title / disclaimer / forward text).
4. Default deliverable = **copy-paste prompts only**; do not call user-paid video APIs
   unless business explicitly asks and confirms cost.
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

Both: not Seedance 五拍；not disease Remotion MG；default copy-paste prompts only.

## Product PPT courseware: guide business in four steps

When extending a settled product courseware template (e.g. green 金银花露):

1. **Select template** first.
2. Accept **partial materials** (even product name only).
3. Produce a **content draft** for business approval (do not skip to final PPT).
4. Generate **PPTX only after draft sign-off**.

Canonical workflow (Chinese, for business + agent):  
`production-library/templates/settled/product-courseware-green-v1/业务使用流程.md`
