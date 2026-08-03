# Library Map

Read only the relevant source:

- Global policy and entrypoints: `production-library/catalog.json`
- Assembly and style-lock rules: `production-library/assembly-protocol.md`
- Style packs and image styles: `production-library/registries/styles.json`
- Video/courseware template families: `production-library/registries/templates.json`
- Scene and UI components: `production-library/registries/components.json`
- Motion and presenter effects: `production-library/registries/effects.json`
- Authorized voice configurations: `production-library/registries/voices.json`
- Script-intent scene recipes: `production-library/registries/scene-recipes.json`
- Script-driven free assembly: `production-library/script-assembly-protocol.md`
- Locked implementation decisions: `production-library/registries/decisions.json`
- Reusable failure-prevention rules: `production-library/registries/lessons.json`
- Image assets: `assets/component-library/*/registry.json`
- Detailed 1080P typography/layout rules: `docs/courseware-visual-spec-1080p.md`
- Complete human correction history: `tasks/lessons.md`

Use `scripts/query_production_library.py` as the normal entrypoint instead of loading every registry.
