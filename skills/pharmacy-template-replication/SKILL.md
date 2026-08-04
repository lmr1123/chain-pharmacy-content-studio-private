---
name: pharmacy-template-replication
description: Query and reuse the chain-pharmacy production library when replicating, extending, or assembling internal health-education videos, product-training courseware, digital presenters, image assets, voices, motion effects, MP4/PDF/PPTX templates, or new disease and product themes. Use this skill before creating new visual styles, assets, components, effects, or template variants in this project.
---

# Pharmacy Template Replication

Use the project production library as the source of truth. Search before creating, lock one style pack per project, and register every approved addition.

Settled templates and validation artifacts are physically separate. Locate approved template
artifacts only through `production-library/templates/settled/` and the template registry.
Treat each settled directory as a complete business handoff bundle: one canonical video/PPTX,
`业务提交_空白模板.docx`, `业务提交_填写参考.docx`, and `manifest.json`. Refresh the
Word copies from the manifest-declared authoritative sources with
`scripts/sync_settled_template_business_words.py`.
Write exploratory renders, QA, comparisons, and rejected variants only under
`production-library/validation/`; never recreate a mixed `out` or `output` directory.

## Locked direction

Follow `AGENTS.md` and `decision.gold-sample-first` (query: `--type decision --text 金样`).  
Gold-sample complete courseware/video first; assets only fill framework slots from a signed gold sample. Business provides packshots.

## Start

1. Read `production-library/assembly-protocol.md` (and `docs/project-brief.md` §1.1 if direction is unclear).
2. Query before inspecting source files:

```bash
python3 scripts/query_production_library.py --text <keyword>
python3 scripts/query_production_library.py --type effect --tag 扫描线
python3 scripts/query_production_library.py \
  --style-pack style-pack.reference-medical-tech-v1 \
  --approved-only
```

3. Read only the matching registry sources. Use `references/library-map.md` to select them.
4. Create or update `tasks/todo.md` before non-trivial work.

## Replicate a Reference

1. Record exact source time range, spoken text, scene nodes, layout ratios, actions, audio characteristics, and transition behavior.
2. Separate facts into:
   - directly observed behavior;
   - measured values;
   - implementation inference;
   - unresolved asset or authorization dependency.
3. Bind one existing `template_id` and one `style_pack_id`.
4. Map the approved script to existing scene types and component slots.
5. Reuse production-validated components and effects before creating variants.
6. Recreate images; never import reference-video pixels into production assets.
7. Validate against the reference before proposing a visual upgrade.

## Assemble a New Theme or Product

Keep the template, style pack, scene recipes, animation grammar, presenter rig, subtitle system, and export settings. Replace only approved content slots, authorized product images, theme assets, and timing.

Do not mix incompatible image styles inside one project. A style pack may explicitly allow multiple asset substyles, such as cartoon symptoms and realistic botanicals; shared cards, color treatment, typography, and motion must still unify them.

Use `production-library/examples/` as assembly contracts, not as approved medical or product content.

## Create a Missing Item

Create a new item only when no registered component can express the requirement through its public parameters.

- For images, sign off one representative image before batch generation.
- For presenters, keep one body anchor and normalized face anchors.
- For speech, generate complete semantic blocks and perform ASR, crossfade, declick, and loudness QA.
- For effects, expose timing, dimensions, color, and intensity as parameters.
- For layouts, centralize editable X/Y, size, spacing, and type-scale values.
- **For small icons / layout marks** (arrows, chevrons, bullets/dots, separators,
  check/cross, info/warning badges, simple objects like pill/heart/stethoscope):
  treat [Koboyo Icons](https://koboyo.com/icons) as the **on-demand source**, not a
  pre-stockpile. Workflow:
  1. Search the site for a matching slug (layout marks and health objects both OK).
  2. Download only the needed SVG(s) to the **local** path
     `assets/_intake/open_source/koboyo/svg/<layout|health>/` (gitignored — do not
     `git add` bulk SVG). Full library mirror is forbidden (license + size).
  3. Recolor `currentColor` to the style pack brand color; rasterize to PNG when
     PPTX/Revideo needs bitmaps; candidates → master after visual check.
     Only approved masters belong in Git under `component-library`.
  4. Do **not** use Koboyo to replace multi-color scene masters (symptoms, advice
     illustrations, pharmacist presenters). Sequence numbers 1–n: prefer text +
     circle shape, not forced digit icons.
  Details: `assets/_intake/open_source/koboyo/SOURCE.md`.

After approval, add a stable ID, tags, status, compatible style pack, source path, and editable parameters to the applicable registry.

## Validate

Require:

- typecheck and full render/decode;
- 1920×1080, 30fps unless the project contract says otherwise;
- no black frames or layout overflow;
- readable 50% preview and effective font sizes;
- stable presenter mouth during speech, pauses, and final frame;
- audio ASR, loudness, and boundary continuity;
- at least two time-separated frames for every claimed dynamic effect;
- traceable source and style ID for every production asset.

Record user corrections in both `tasks/lessons.md` and the structured lesson registry when broadly reusable.
