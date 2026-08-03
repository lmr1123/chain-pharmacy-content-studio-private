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

## Business + WorkBuddy default entry (no unzip)

Business opens WorkBuddy and says:

```text
请安装 https://github.com/lmr1123/chain-pharmacy-content-studio.git，然后指引我使用
```

Agent must: install/update repo (`scripts/workbuddy_bootstrap_for_business.py`), open the
guided portal, then walk **preview → Word fill → submit → draft → final**.
See `docs/workbuddy-install-and-guide.md` and `docs/workbuddy-system-prompt.md`.
Do **not** tell business to unzip a zip as the default path.

## Product PPT courseware: guide business in four steps

When extending a settled product courseware template (e.g. green 金银花露):

1. **Select template** first.
2. Accept **partial materials** (even product name only).
3. Produce a **content draft** for business approval (do not skip to final PPT).
4. Generate **PPTX only after draft sign-off**.

Canonical workflow (Chinese, for business + agent):  
`production-library/templates/settled/product-courseware-green-v1/业务使用流程.md`
