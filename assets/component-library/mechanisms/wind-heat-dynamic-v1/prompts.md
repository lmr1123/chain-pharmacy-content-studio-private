# 生成提示词与参考边界

生成器：内置 `image_gen`。四张用户截图分别只承担构图、人体细节等级和症状表达参考；生成全新原创画面，不复制参考像素，不保留截图中的字幕、界面、Logo 或水印。

## 全身风热入侵

```text
Scientific-educational production asset for a 1920x1080 pharmacy training animation. Create one original, gender-neutral, smooth cyan-blue translucent medical scan figure, full body, frontal neutral stance, anatomically plausible adult proportions, soft volumetric inner light and polished 3D surface. Match only the reference's low-detail smooth silhouette and clinical cyan palette. No exposed anatomy, no muscles, skeleton, veins, text, icons, UI, logo or watermark. Isolate the figure on a perfectly uniform #ff00ff chroma-key background with clean complete hands and feet and generous padding.
```

## 体表受邪与肺部

```text
Scientific-educational original medical illustration. Smooth translucent cyan-blue upper-body adult figure, slightly bowed with both hands over the chest; clearly visible stylized coral-red lungs inside the torso, gentle clinical 3D rendering, no gore. Preserve only the reference's composition and symptom focus. No purple smoke, labels, UI, logo or watermark because those are animated as separate layers. Uniform #ff00ff chroma-key background, complete isolated subject, clean edges.
```

## 咽喉聚焦

```text
Scientific-educational original medical visualization. Smooth translucent cyan-blue head, neck and upper torso facing forward, premium soft 3D scan surface, neutral expression, simplified anatomy and no exposed internal detail. Keep the throat area unobstructed for a separate animated red symptom glow. No baked glow, text, UI, logo or watermark. Uniform #ff00ff chroma-key background and clean isolated edges.
```

## 喉部剖面与气流

```text
Scientific-educational original medical visualization. Side-profile cyan-blue translucent head, neck and upper chest with a clean simplified coral airway/larynx cutaway, polished clinical 3D style and non-graphic anatomy. Keep the larynx region clear for separate animated red glow and airflow particles. No baked symptom glow, text, labels, UI, logo or watermark. Uniform #ff00ff chroma-key background with clean isolated edges.
```

## 体表受邪体积邪气

```text
Scientific-educational production background texture. Create layered purple and indigo pathogenic mist shaped like soft flame tongues and curling vapor plumes, rising from both lower sides around a large empty central silhouette-safe zone. Use translucent depth, luminous lavender rims, darker violet cores, feathered edges, overlapping foreground/background layers and natural asymmetry. Uniform deep navy #102230 background to every edge. No person, anatomy, lungs, text, UI, frame, logo or watermark. Do not create thin strokes, repeated wave symbols, flat vector lines, particles or a symmetrical decorative pattern.
```

生成两张相邻运动相位：B 相位保持同一背景与中心安全区，但将左右气体的上涌、内卷和亮边位置改成约 0.7 秒后的形态，用于交叉过渡和分层漂移。
