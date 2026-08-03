from pathlib import Path

from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


WORK_DIR = Path(__file__).resolve().parent
REPO_DIR = WORK_DIR.parents[2]
SOURCE_DIR = (
    REPO_DIR
    / "production-library"
    / "validation"
    / "courseware"
    / "disease-product-scenario-v1"
    / "qa-editable"
)
OUTPUT = (
    REPO_DIR
    / "production-library"
    / "validation"
    / "courseware"
    / "disease-product-scenario-v1"
    / "穿心莲内酯滴丸_商品培训课件2_可编辑重建版.pdf"
)
PAGE_WIDTH = 960
PAGE_HEIGHT = 540


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(OUTPUT), pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    for source in sorted(SOURCE_DIR.glob("slide-??.png")):
        with Image.open(source) as image:
            width, height = image.size
        scale = min(PAGE_WIDTH / width, PAGE_HEIGHT / height)
        draw_width = width * scale
        draw_height = height * scale
        left = (PAGE_WIDTH - draw_width) / 2
        bottom = (PAGE_HEIGHT - draw_height) / 2
        pdf.drawImage(
            ImageReader(str(source)),
            left,
            bottom,
            width=draw_width,
            height=draw_height,
            preserveAspectRatio=True,
            mask="auto",
        )
        pdf.showPage()
    pdf.save()
    print(OUTPUT)


if __name__ == "__main__":
    main()
