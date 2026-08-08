# recipes（引擎侧占位）

正式页型 recipe 与 cw4 映射在：

`production-library/page-types/product-training/recipes/`

- `*.json` — 各 page_type 构件组合声明 + `impl_by_scene`
- `scene-type-map.json` — content-model `scene.type` → `page_type` + builder `impl`

export 默认加载上述目录；本目录不放业务 recipe。

**新页型（L1 生长通道）：** 勿直接改本占位目录。  
走 `docs/page-type-growth-channel.md` → 提案落在 `page-types/product-training/proposals/` → 签样后写正式 recipe。
