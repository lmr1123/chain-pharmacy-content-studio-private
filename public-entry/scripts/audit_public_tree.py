#!/usr/bin/env python3
"""Self-audit an exported Public installer tree against its SHA-256 manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


MANIFEST_NAME = "SHA256SUMS.json"
EXPECTED_FILES = {
    ".github/workflows/public-audit.yml",
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "SECURITY.md",
    "scripts/audit_public_tree.py",
    "scripts/install_private_studio.py",
}
EXPECTED_MAX_FILE_BYTES = 65536
EXPECTED_MAX_TOTAL_BYTES = 262144
EXPECTED_PUBLIC_REPOSITORY = "lmr1123/chain-pharmacy-content-studio"
EXPECTED_PRIVATE_REPOSITORY = "lmr1123/chain-pharmacy-content-studio-private"
ALLOWED_SUFFIXES = {".md", ".py", ".json", ".yml", ".yaml"}
ALLOWED_BASENAMES = {".gitignore"}
FORBIDDEN_SUFFIXES = {
    ".7z", ".avi", ".doc", ".docx", ".eot", ".gif", ".gz", ".ico",
    ".jpeg", ".jpg", ".m4a", ".mkv", ".mov", ".mp3", ".mp4", ".odp",
    ".ods", ".odt", ".otf", ".pdf", ".png", ".ppt", ".pptx", ".rar",
    ".tar", ".tif", ".tiff", ".ttf", ".wav", ".webm", ".webp", ".woff",
    ".woff2", ".xls", ".xlsx", ".zip",
}
SECRET_PATTERNS = (
    re.compile("gh" + r"p_[A-Za-z0-9]{20,}"),
    re.compile("github" + r"_pat_[A-Za-z0-9_]{20,}"),
    re.compile("-----BEGIN " + r"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(
        r"(?i)(?:api[_-]?key|password|secret|token)\s*[:=]\s*['\"][^'\"\n]{8,}['\"]"
    ),
)
FORBIDDEN_SIGNATURES = (
    b"PK\x03\x04",
    b"PK\x05\x06",
    b"PK\x07\x08",
    b"\x89PNG\r\n\x1a\n",
    b"\xff\xd8\xff",
    b"GIF87a",
    b"GIF89a",
    b"RIFF",
    b"wOFF",
    b"wOF2",
    b"OTTO",
    b"ttcf",
    b"%PDF-",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _tree_entries(root: Path) -> tuple[set[str], list[str]]:
    files: set[str] = set()
    symlinks: list[str] = []
    for current, directories, names in os.walk(root, followlinks=False):
        current_path = Path(current)
        directories[:] = [
            name for name in directories if name not in {".git", "__pycache__"}
        ]
        for name in list(directories):
            path = current_path / name
            if path.is_symlink():
                symlinks.append(path.relative_to(root).as_posix())
                directories.remove(name)
        for name in names:
            if name.endswith(".pyc"):
                continue
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                symlinks.append(relative)
            elif path.is_file():
                files.add(relative)
    return files, symlinks


def _history_errors(root: Path) -> list[str]:
    if not (root / ".git").exists():
        return []
    errors: list[str] = []
    allowed = EXPECTED_FILES | {MANIFEST_NAME}
    try:
        objects = subprocess.run(
            ["git", "-C", str(root), "rev-list", "--objects", "--all"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ["unable to inspect Public git history"]
    if objects.returncode != 0:
        return ["unable to inspect Public git history"]
    try:
        typed_objects = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "cat-file",
                "--batch-check=%(objecttype) %(objectname) %(rest)",
            ],
            input=objects.stdout,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ["unable to inspect Public git object types"]
    if typed_objects.returncode != 0:
        return ["unable to inspect Public git object types"]
    historical_paths = set()
    for line in typed_objects.stdout.splitlines():
        parts = line.split(" ", 2)
        if len(parts) == 3 and parts[0] == "blob":
            historical_paths.add(parts[2])
    for path in sorted(historical_paths - allowed):
        errors.append(f"forbidden historical path: {path}")

    try:
        patches = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "log",
                "--all",
                "-p",
                "--no-ext-diff",
                "--text",
                "--pretty=format:",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return errors + ["unable to scan Public git history for secrets"]
    if patches.returncode != 0:
        return errors + ["unable to scan Public git history for secrets"]
    for pattern in SECRET_PATTERNS:
        if pattern.search(patches.stdout):
            errors.append("possible secret in Public git history")
            break
    return errors


def audit_tree(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.is_file() or manifest_path.is_symlink():
        return [f"missing safe manifest: {MANIFEST_NAME}"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"invalid manifest: {exc}"]
    if manifest.get("default_action") != "deny":
        errors.append("manifest must remain default-deny")
    if manifest.get("history_policy") != "new-repository-only":
        errors.append("invalid Public history policy")
    if manifest.get("public_repository") != EXPECTED_PUBLIC_REPOSITORY:
        errors.append("invalid Public repository identity")
    if manifest.get("private_repository") != EXPECTED_PRIVATE_REPOSITORY:
        errors.append("invalid Private repository identity")

    declared_items = manifest.get("files")
    if not isinstance(declared_items, list):
        return ["manifest files must be a list"]
    declared: dict[str, dict] = {}
    for item in declared_items:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            errors.append("invalid manifest file entry")
            continue
        path = item["path"]
        if path in declared or Path(path).is_absolute() or ".." in Path(path).parts:
            errors.append(f"unsafe or duplicate manifest path: {path}")
            continue
        declared[path] = item
    if set(declared) != EXPECTED_FILES:
        errors.append("manifest paths do not match the exact Public allowlist")

    actual, symlinks = _tree_entries(root)
    for path in symlinks:
        errors.append(f"symlink forbidden: {path}")
    expected = set(declared) | {MANIFEST_NAME}
    for path in sorted(actual - expected):
        errors.append(f"unexpected file: {path}")
    for path in sorted(expected - actual):
        errors.append(f"missing file: {path}")

    max_file = manifest.get("max_file_bytes")
    max_total = manifest.get("max_total_bytes")
    if max_file != EXPECTED_MAX_FILE_BYTES:
        errors.append("invalid max_file_bytes")
        max_file = EXPECTED_MAX_FILE_BYTES
    if max_total != EXPECTED_MAX_TOTAL_BYTES:
        errors.append("invalid max_total_bytes")
        max_total = EXPECTED_MAX_TOTAL_BYTES
    total = 0
    for relative, item in sorted(declared.items()):
        path = root / relative
        if not path.is_file() or path.is_symlink():
            continue
        suffix = path.suffix.lower()
        if suffix in FORBIDDEN_SUFFIXES or (
            suffix not in ALLOWED_SUFFIXES and path.name not in ALLOWED_BASENAMES
        ):
            errors.append(f"forbidden file type: {relative}")
        size = path.stat().st_size
        total += size
        if max_file and size > max_file:
            errors.append(f"file too large: {relative}")
        if item.get("bytes") != size:
            errors.append(f"size mismatch: {relative}")
        if item.get("sha256") != _sha256(path):
            errors.append(f"sha256 mismatch: {relative}")
        payload = path.read_bytes()
        if any(payload.startswith(signature) for signature in FORBIDDEN_SIGNATURES) or (
            len(payload) >= 12 and payload[4:8] == b"ftyp"
        ):
            errors.append(f"binary/media signature forbidden: {relative}")
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            errors.append(f"non-text content forbidden: {relative}")
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"possible secret: {relative}")
                break
    if max_total and total > max_total:
        errors.append("tree too large")
    manifest_size = manifest_path.stat().st_size
    if manifest_size > max_file:
        errors.append("manifest too large")
    if total + manifest_size > max_total:
        errors.append("tree including manifest too large")
    if manifest.get("total_bytes") != total:
        errors.append("manifest total_bytes mismatch")
    errors.extend(_history_errors(root))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    args = parser.parse_args()
    errors = audit_tree(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Public installer audit: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
