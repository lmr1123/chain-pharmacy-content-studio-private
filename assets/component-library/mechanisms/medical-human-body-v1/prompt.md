# 生成提示词

使用内置 `image_gen` 生成，参考帧只用于理解主体类别、正面比例和蓝色医学扫描质感，不复制参考像素。

```text
Use case: scientific-educational.
Asset type: production-ready isolated medical human body visual for a 1920x1080 Chinese pharmacy training video.
Reference role: use the attached video frame only to understand the intended subject category, frontal proportions, blue medical scan aesthetic, and full-body framing. Create a completely new original image; do not reproduce any reference pixels, presenter, interface, logo, text, or surrounding icons.
Primary subject: one anatomically plausible adult human figure, standing straight in neutral anatomical posture, facing directly forward, arms relaxed slightly away from torso, feet shoulder-width apart. Full body from head to toes, centered, generous padding, realistic adult proportions and recognizable hands and feet.
Style/medium: premium realistic 3D medical visualization, translucent cyan-blue body with softly visible musculature, skeletal landmarks and subtle internal vascular/respiratory structures, polished clinical scan rendering, luminous cyan rim light, controlled soft inner glow. No exposed gore, no genital detail, educational and non-graphic.
Composition: single isolated figure only, symmetrical frontal view, no base platform, no floor, no cast shadow.
Background extraction requirement: perfectly flat solid #ff00ff chroma-key background, absolutely uniform with no gradients, texture, reflections, shadows, fog, glow spill, or lighting variation in the background. Keep the figure fully separated from the background with crisp clean edges. Do not use #ff00ff anywhere in the figure.
Constraints: no words, no labels, no UI, no logo, no watermark, no extra objects, no duplicate limbs, no cropped fingers or toes. The final figure should read as a finished high-end medical illustration, not SVG, not wireframe, not a mannequin silhouette, not a rough concept.
```
