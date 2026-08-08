#!/usr/bin/env python3
"""Export the exact, sanitized Public installer tree with a deterministic manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "public-entry"
DEFAULT_POLICY = ROOT / "distribution/public-installer-policy.json"
PUBLIC_REPOSITORY = "lmr1123/chain-pharmacy-content-studio"
PRIVATE_REPOSITORY = "lmr1123/chain-pharmacy-content-studio-private"
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
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
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


def _load_policy(path: Path) -> dict:
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid public installer policy: {exc}") from exc
    allowed = policy.get("allowed_source_paths")
    generated = policy.get("generated_paths")
    if (
        policy.get("schema_version") != 1
        or policy.get("default_action") != "deny"
        or policy.get("source_root") != "public-entry"
        or policy.get("public_repository") != PUBLIC_REPOSITORY
        or policy.get("private_repository") != PRIVATE_REPOSITORY
        or policy.get("history_policy") != "new-repository-only"
        or not isinstance(allowed, list)
        or not allowed
        or allowed != sorted(set(allowed))
        or generated != ["SHA256SUMS.json"]
        or not isinstance(policy.get("max_file_bytes"), int)
        or policy["max_file_bytes"] <= 0
        or not isinstance(policy.get("max_total_bytes"), int)
        or policy["max_total_bytes"] <= 0
    ):
        raise SystemExit("invalid public installer policy structure")
    for relative in allowed:
        if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise SystemExit(f"unsafe allowlisted path: {relative}")
    return policy


def _source_entries(source: Path) -> tuple[set[str], list[str]]:
    files: set[str] = set()
    symlinks: list[str] = []
    for current, directories, names in os.walk(source, followlinks=False):
        current_path = Path(current)
        directories[:] = [name for name in directories if name != "__pycache__"]
        for name in list(directories):
            path = current_path / name
            if path.is_symlink():
                symlinks.append(path.relative_to(source).as_posix())
                directories.remove(name)
        for name in names:
            if name.endswith(".pyc"):
                continue
            path = current_path / name
            relative = path.relative_to(source).as_posix()
            if path.is_symlink():
                symlinks.append(relative)
            elif path.is_file():
                files.add(relative)
    return files, symlinks


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _validated_payload(path: Path, relative: str, max_bytes: int) -> bytes:
    suffix = path.suffix.lower()
    if suffix in FORBIDDEN_SUFFIXES or (
        suffix not in ALLOWED_SUFFIXES and path.name not in ALLOWED_BASENAMES
    ):
        raise SystemExit(f"forbidden public file type: {relative}")
    payload = path.read_bytes()
    if len(payload) > max_bytes:
        raise SystemExit(f"public file too large: {relative}")
    if any(payload.startswith(signature) for signature in FORBIDDEN_SIGNATURES) or (
        len(payload) >= 12 and payload[4:8] == b"ftyp"
    ):
        raise SystemExit(f"binary/media signature forbidden: {relative}")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SystemExit(f"non-text public content forbidden: {relative}") from exc
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            raise SystemExit(f"possible secret in public file: {relative}")
    return payload


def export_public_installer(source: Path, destination: Path, policy_path: Path) -> Path:
    if source.is_symlink() or not source.is_dir():
        raise SystemExit(f"unsafe or missing public source: {source}")
    if destination.exists() or destination.is_symlink():
        raise SystemExit(f"public export destination already exists: {destination}")
    policy = _load_policy(policy_path)
    allowed = set(policy["allowed_source_paths"])
    actual, symlinks = _source_entries(source)
    if symlinks:
        raise SystemExit(f"symlink forbidden in public source: {sorted(symlinks)[0]}")
    extra = sorted(actual - allowed)
    missing = sorted(allowed - actual)
    if extra:
        raise SystemExit(f"public source path is not allowlisted: {extra[0]}")
    if missing:
        raise SystemExit(f"allowlisted public source path is missing: {missing[0]}")

    payloads: dict[str, bytes] = {}
    total = 0
    for relative in sorted(allowed):
        payload = _validated_payload(
            source / relative, relative, policy["max_file_bytes"]
        )
        total += len(payload)
        if total > policy["max_total_bytes"]:
            raise SystemExit("public installer tree too large")
        payloads[relative] = payload

    manifest = {
        "schema_version": 1,
        "default_action": policy["default_action"],
        "history_policy": policy["history_policy"],
        "public_repository": policy["public_repository"],
        "private_repository": policy["private_repository"],
        "files": [
            {
                "path": relative,
                "bytes": len(payloads[relative]),
                "sha256": _sha256_bytes(payloads[relative]),
            }
            for relative in sorted(payloads)
        ],
        "max_file_bytes": policy["max_file_bytes"],
        "max_total_bytes": policy["max_total_bytes"],
        "total_bytes": total,
    }
    manifest_bytes = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    if len(manifest_bytes) > policy["max_file_bytes"]:
        raise SystemExit("public manifest too large")
    if total + len(manifest_bytes) > policy["max_total_bytes"]:
        raise SystemExit("public installer tree including manifest too large")

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.name}.export-", dir=str(destination.parent)
        )
    )
    try:
        for relative, payload in payloads.items():
            output = staging / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(payload)
        (staging / "SHA256SUMS.json").write_bytes(manifest_bytes)
        os.replace(staging, destination)
    finally:
        if staging.exists() and staging.is_dir() and not staging.is_symlink():
            shutil.rmtree(staging)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    args = parser.parse_args()
    output = export_public_installer(args.source, args.destination, args.policy)
    print(f"Public installer exported: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
