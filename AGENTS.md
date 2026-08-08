# Project-specific production rule

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

**Locked model:** business provides content in chat; **WorkBuddy on the business machine**
produces PPT / product video / health video. Do **not** bounce normal settled work to
「请找制作」or require the engineer to run renders.

Agent must: `git pull` + `scripts/workbuddy_bootstrap_for_business.py`, open the portal,
then on content: lock template → organize → **run generators**.
Before render: `python3 scripts/probe_production_env.py` (honest degrade if no TTS/ffmpeg).
- PPT / 绿色单品等：各 settled generator  
- 课件3：`scripts/generate_business_courseware.py --template courseware3 --theme <dir>`  
- 视频：`generate_business_video.py --mode full`（product 8 / health 7 segments）；never default `audio-shell`  
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

## Product PPT courseware: guide business in four steps

When extending a settled product courseware template (e.g. green 金银花露):

1. **Select template** first.
2. Accept **partial materials** (even product name only).
3. Produce a **content draft** for business approval (do not skip to final PPT).
4. Generate **PPTX only after draft sign-off**.

Canonical workflow (Chinese, for business + agent):  
`production-library/templates/settled/product-courseware-green-v1/业务使用流程.md`
