#!/usr/bin/env python3
"""Refresh business Word files beside settled templates.

SSOT for mappings: scripts/build_business_word_guides.py
This entrypoint remains for backward compatibility.
"""

from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    target = Path(__file__).resolve().parent / "build_business_word_guides.py"
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    main()
