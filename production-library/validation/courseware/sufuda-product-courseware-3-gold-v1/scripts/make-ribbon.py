#!/usr/bin/env python3
"""重生成章节 ribbon：1400×200（原 700×100 的 2 倍），同名替换 public/assets/ribbon-chapter-shell-v1.png。

几何来自原图像素扫描：主带 #e98200（y 10..90，x 44..656 @700×100），
两端燕尾折角 #c86400，缺角顶点约在 (18,50) / (682,50)。4× 超采样抗锯齿。
"""
from PIL import Image, ImageDraw

W, H = 1400, 200
SS = 4  # supersample
ORANGE = (233, 130, 0, 255)
FOLD = (200, 100, 0, 255)

img = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0))
d = ImageDraw.Draw(img)


def S(pts):
    return [(x * SS, y * SS) for x, y in pts]


# 主带
d.rectangle([88 * SS, 20 * SS, 1312 * SS, 180 * SS], fill=ORANGE)
# 左燕尾（缺角朝内的五边形）
d.polygon(S([(40, 100), (0, 40), (88, 20), (88, 180), (0, 160)]), fill=FOLD)
# 右燕尾（镜像）
d.polygon(S([(1360, 100), (1400, 40), (1312, 20), (1312, 180), (1400, 160)]), fill=FOLD)

img = img.resize((W, H), Image.LANCZOS)
out = 'public/assets/ribbon-chapter-shell-v1.png'
img.save(out)
print('written', out, img.size)
