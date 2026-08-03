#!/usr/bin/env python3
"""One-shot: words + guides + previews + tier-A package + content-driven tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(script: str) -> None:
    print(f"\n>>> {script}")
    subprocess.check_call([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT)


def main() -> None:
    run("build_business_word_guides.py")
    run("sync_settled_template_previews.py")
    run("build_business_tier_a_package.py")
    run("test_content_driven_rules.py")
    print("\nAll business-delivery refresh steps OK.")
    print("Package: outputs/业务使用资料包/药店培训内容工厂-业务包.zip")


if __name__ == "__main__":
    main()
