#!/usr/bin/env python3
"""Build UTF-8 ZIP files for the business-facing content input packages."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


REPO_DIR = Path("/Users/liminrong/Projects/chain-pharmacy-content-studio")
PACKAGE_ROOT = REPO_DIR / "outputs/业务使用资料包"
PACKAGE_NAMES = [
    "01_健康知识视频培训_业务内容整理包",
    "02_商品培训视频课件_业务内容整理包",
    "03_通用PPTX培训课件_业务内容整理包",
]


def write_directory_archive(directory: Path, output: Path) -> None:
    with ZipFile(output, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.name != ".DS_Store":
                archive.write(path, path.relative_to(directory.parent))


def main() -> None:
    archives: list[Path] = []
    for name in PACKAGE_NAMES:
        directory = PACKAGE_ROOT / name
        output = PACKAGE_ROOT / f"{name}.zip"
        write_directory_archive(directory, output)
        archives.append(output)

    bundle = PACKAGE_ROOT / "业务内容整理资料包_全部类型.zip"
    with ZipFile(bundle, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        archive.write(PACKAGE_ROOT / "总说明.txt", "总说明.txt")
        for path in archives:
            archive.write(path, path.name)

    for path in [*archives, bundle]:
        print(path)


if __name__ == "__main__":
    main()
