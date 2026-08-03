# generic-coq10-packshot-v1

- 工具：内置 `imagegen`
- 用途：商品培训模板签样中的无品牌包装示意
- 参考图：无
- 真实品牌包装：未使用
- 参考视频像素：未使用

## Prompt

```text
Use case: product-mockup
Asset type: editable internal pharmaceutical training video product hero cutout
Primary request: create a polished generic coenzyme Q10 medicine packshot consisting of one upright rectangular medicine carton and one short white opaque plastic tablet bottle with a white screw cap, arranged as a balanced pair, three-quarter front view. The carton front has a clean blank cream label panel and a restrained coral-red lower color block; the bottle has a matching blank cream label panel with coral-red lower band. No real brand identity and no copied packaging.
Scene/backdrop: perfectly flat solid #00ff00 chroma-key background for background removal; one uniform color with no shadows, gradients, texture, reflections, floor plane, or lighting variation.
Style/medium: premium clean 3D product mockup, crisp silhouette, matte pharmaceutical packaging, suitable for a 1920x1080 corporate training slide.
Composition/framing: full carton and bottle visible with generous padding, centered, bottle slightly in front of carton, no cropping.
Lighting/mood: soft neutral studio illumination on the objects only; clean and trustworthy.
Color palette: warm white, cream, restrained coral red, tiny dark charcoal details; do not use green anywhere in the product.
Text: no text, no letters, no numbers, no logos.
Constraints: opaque simple edges for reliable chroma-key removal; accurate packaging geometry; no cast shadow, no contact shadow, no reflection, no watermark.
Avoid: recognizable pharmaceutical brands, real packaging, capsules or loose pills, medical claims, extra props, green product colors, warped labels, illegible pseudo-text.
```

## 后处理

- 使用 `remove_chroma_key.py` 移除纯色背景。
- 输出包含 alpha 通道。
- 包装名称、规格和卖点不写入位图，由模板文字层独立绘制。
