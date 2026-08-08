#!/usr/bin/env python3
"""Validate settled-template truth used by business self-service.

This validator deliberately separates an approved gold sample from an executable
business workflow. It does not render media; it checks references and capability
claims before the portal or business package is published.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CAPABILITY_KEYS = {
    "gold_viewable",
    "content_draft",
    "new_theme_preview",
    "new_theme_pptx",
    "new_theme_mp4",
    "business_selfserve",
}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_relpaths(manifest: dict) -> set[str]:
    paths: set[str] = set()
    artifact = manifest.get("canonical_artifact")
    if isinstance(artifact, str):
        paths.add(artifact)
    elif isinstance(artifact, dict) and isinstance(artifact.get("path"), str):
        paths.add(artifact["path"])
    artifacts = manifest.get("canonical_artifacts")
    if isinstance(artifacts, dict):
        for item in artifacts.values():
            if isinstance(item, str):
                paths.add(item)
            elif isinstance(item, dict) and isinstance(item.get("path"), str):
                paths.add(item["path"])
    return paths


def _registry_canonical_relpath(item: dict, settled_dir: str) -> str | None:
    artifact = item.get("canonical_artifact")
    path: str | None = None
    if isinstance(artifact, str):
        path = artifact
    elif isinstance(artifact, dict) and isinstance(artifact.get("path"), str):
        path = artifact["path"]
    if not path:
        return None
    prefix = settled_dir.rstrip("/") + "/"
    return path[len(prefix) :] if path.startswith(prefix) else path


def validate_repository(root: Path) -> dict[str, Any]:
    root = root.resolve()
    settled_root = root / "production-library/templates/settled"
    catalog = _load(settled_root / "business-catalog.json")
    template_registry = _load(root / "production-library/registries/templates.json")
    style_registry = _load(root / "production-library/registries/styles.json")
    voice_registry = _load(root / "production-library/registries/voices.json")

    errors: list[str] = []
    warnings: list[str] = []
    style_ids = {item.get("id") for item in style_registry.get("items", [])}
    voice_by_id = {
        item.get("id"): item
        for item in voice_registry.get("items", [])
        if item.get("id")
    }
    voice_ids = set(voice_by_id)
    registry_by_dir = {
        item.get("settled_template_dir"): item
        for item in template_registry.get("items", [])
        if item.get("settled_template_dir")
    }

    seen: set[str] = set()
    for template in catalog.get("templates", []):
        slug = template.get("slug")
        if not isinstance(slug, str) or not slug:
            errors.append("business catalog contains a template without slug")
            continue
        if slug in seen:
            errors.append(f"{slug}: duplicate business catalog slug")
            continue
        seen.add(slug)

        capabilities = template.get("capabilities")
        if not isinstance(capabilities, dict):
            errors.append(f"{slug}: missing capabilities matrix")
            capabilities = {}
        missing = sorted(CAPABILITY_KEYS - set(capabilities))
        if missing:
            errors.append(f"{slug}: missing capability keys: {', '.join(missing)}")
        for key in CAPABILITY_KEYS & set(capabilities):
            if type(capabilities[key]) is not bool:
                errors.append(f"{slug}: capability {key} must be boolean")
        if template.get("production_ready") is not capabilities.get("business_selfserve"):
            errors.append(f"{slug}: production_ready must derive from business_selfserve")
        if not isinstance(template.get("requirements"), list):
            errors.append(f"{slug}: requirements must be a list")
        if not isinstance(template.get("blockers"), list):
            errors.append(f"{slug}: blockers must be a list")

        expected_dir = f"production-library/templates/settled/{slug}"
        if template.get("settled_dir") != expected_dir:
            errors.append(f"{slug}: settled_dir must be {expected_dir}")
        settled_dir = root / expected_dir
        if not settled_dir.is_dir():
            errors.append(f"{slug}: settled directory is missing")
            continue

        manifest_path = settled_dir / "manifest.json"
        if not manifest_path.is_file():
            errors.append(f"{slug}: manifest.json is missing")
            continue
        manifest = _load(manifest_path)
        registry = registry_by_dir.get(expected_dir)
        if not registry:
            errors.append(f"{slug}: template registry has no matching settled_template_dir")
            continue
        if manifest.get("template_id") != registry.get("id"):
            errors.append(
                f"{slug}: manifest template_id {manifest.get('template_id')} != registry {registry.get('id')}"
            )
        if manifest.get("style_pack_id") != registry.get("style_pack_id"):
            errors.append(f"{slug}: manifest and registry style_pack_id differ")
        style_id = manifest.get("style_pack_id")
        if style_id not in style_ids:
            errors.append(f"{slug}: unregistered style_pack_id {style_id}")

        voice_id = template.get("voice_id")
        if voice_id and voice_id not in voice_ids:
            errors.append(f"{slug}: unregistered voice_id {voice_id}")
        elif voice_id:
            voice_entry = voice_by_id[voice_id]
            voice_dir_value = voice_entry.get("voice_pack_dir")
            voice_dir = root / str(voice_dir_value or "")
            voice_manifest = voice_dir / "voice-pack.json"
            if not voice_dir_value or not voice_manifest.is_file():
                errors.append(f"{slug}: voice pack manifest missing for {voice_id}")
            else:
                voice_pack = _load(voice_manifest)
                prompt = voice_pack.get("prompt") or {}
                prompt_audio = prompt.get("audio")
                if voice_pack.get("id") != voice_id:
                    errors.append(f"{slug}: voice pack id differs from catalog voice_id")
                if (
                    not isinstance(prompt_audio, str)
                    or not (voice_dir / prompt_audio).is_file()
                    or not str(prompt.get("ref_text") or "").strip()
                ):
                    errors.append(f"{slug}: voice pack prompt audio/ref_text is incomplete")

        manifest_canonicals = _canonical_relpaths(manifest)
        if not manifest_canonicals:
            errors.append(f"{slug}: manifest declares no canonical artifact")
        for relpath in sorted(manifest_canonicals):
            if not (settled_dir / relpath).is_file():
                errors.append(f"{slug}: canonical artifact is missing: {relpath}")
        registry_canonical = _registry_canonical_relpath(registry, expected_dir)
        if registry_canonical and registry_canonical not in manifest_canonicals:
            errors.append(
                f"{slug}: registry canonical {registry_canonical} is not in manifest canonical set"
            )

        for required in ("业务提交_空白模板.docx", "业务提交_填写参考.docx"):
            if not (settled_dir / required).is_file():
                errors.append(f"{slug}: missing business file {required}")

        business_input = manifest.get("business_input") or {}
        for copy_key, source_key in (
            ("blank_word", "blank_source"),
            ("filled_example", "example_source"),
        ):
            copy_name = business_input.get(copy_key)
            source_name = business_input.get(source_key)
            if not isinstance(copy_name, str) or not isinstance(source_name, str):
                errors.append(f"{slug}: business_input lacks {copy_key}/{source_key}")
                continue
            source = root / source_name
            copy = settled_dir / copy_name
            if not source.is_file():
                errors.append(f"{slug}: authoritative Word source is missing: {source_name}")
            elif copy.is_file() and source.read_bytes() != copy.read_bytes():
                errors.append(f"{slug}: stale business Word copy: {copy_name}")

        greenline = manifest.get("business_greenline") or {}
        formal_command = str(greenline.get("with_audio_mp4") or "")
        if slug == "health-video-reference-tech-v1":
            if "--theme-package" not in formal_command:
                errors.append(f"{slug}: formal command must require --theme-package")
            if "--skip-visual-approval" in formal_command:
                errors.append(f"{slug}: formal command may not skip visual approval")
        if slug == "product-video-faithful-v1":
            if "--product-image" not in formal_command:
                errors.append(f"{slug}: formal command must require --product-image")
            if "--product-approval" not in formal_command:
                errors.append(f"{slug}: formal command must require --product-approval")

        preview = manifest.get("preview") or {}
        if preview.get("capabilities") != capabilities:
            errors.append(f"{slug}: manifest preview capabilities differ from business catalog")
        if preview.get("requirements") != template.get("requirements"):
            errors.append(f"{slug}: manifest preview requirements differ from business catalog")
        if preview.get("blockers") != template.get("blockers"):
            errors.append(f"{slug}: manifest preview blockers differ from business catalog")
        if preview.get("production_ready") is not capabilities.get("business_selfserve"):
            errors.append(f"{slug}: manifest preview production_ready is stale")
        preview_paths = [preview.get("cover"), *(preview.get("key_frames") or [])]
        for relpath in preview_paths:
            if not isinstance(relpath, str) or not (settled_dir / relpath).is_file():
                errors.append(f"{slug}: missing preview file {relpath!r}")

        if capabilities.get("business_selfserve") and template.get("blockers"):
            warnings.append(f"{slug}: marked self-serve but still lists blockers")

    return {
        "ok": not errors,
        "template_count": len(seen),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = validate_repository(args.root)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("PASS" if report["ok"] else "FAIL")
        for item in report["errors"]:
            print(f"ERROR {item}")
        for item in report["warnings"]:
            print(f"WARN  {item}")
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
