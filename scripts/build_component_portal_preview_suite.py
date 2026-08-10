#!/usr/bin/env python3
"""Promote the reviewed r4 component UAT decks into the portal preview suite."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from sync_settled_template_previews import (
    COMPONENT_PREVIEW_QA_DIR,
    COMPONENT_PREVIEW_QA_SCHEMA,
    COMPONENT_PREVIEW_STYLE_LABEL_ZH,
    DEFAULT_GENERAL_TEMPLATE,
    component_preview_qa_failures,
    component_preview_visual_frame_metrics,
    component_preview_visual_metrics,
)


REPO = Path(__file__).resolve().parents[1]
DEFAULT_JOBS_ROOT = REPO / "outputs/workbuddy-workspaces/uat/jobs"
DEFAULT_DELIVERY_ROOT = REPO / "outputs/workbuddy-workspaces/uat/delivery"
STYLE_PACK_ID = "style-pack.reference-product-blue-v1"
ROUTE_ID = "product-pptx-component-v1"
VISUAL_REVIEW_SCHEMA = "component-portal-preview-visual-review-v1"

PLACEHOLDER_MARKERS = (
    "{{",
    "}}",
    "[tbd]",
    "[todo]",
    "lorem ipsum",
    "placeholder",
    "待补充字段",
    "待替换内容",
)
GOLD_RESIDUAL_MARKERS = (
    "番茄红素",
    "福尔",
    "维生素e",
    "好物推荐",
    "穿心莲",
    "速福达",
    "玛巴洛沙韦",
    "辅酶q10",
    "极信",
)
SOURCE_CAPABILITY_SLUGS = {
    "green": "product-courseware-green-v1",
    "disease": "disease-product-scenario-v1",
    "sufuda": "sufuda-mabaloshawei-product-courseware-3-v1",
}


@dataclass(frozen=True)
class CaseSpec:
    slot: str
    case_id: str
    name_zh: str
    fixture_dir: str
    expected_deck_sha256: str
    reviewed_page_sha256: tuple[str, ...]
    expected_capabilities: tuple[str, ...]
    expected_new_page_types: tuple[str, ...]
    key_pages: tuple[int, ...]
    portal_key_index: int
    crop_key_index: int | None = None
    crop_box_px: tuple[int, int, int, int] | None = None

    @property
    def job_id(self) -> str:
        return f"uat-component-suite-{self.slot.lower()}-20260810-r4"


CASES = (
    CaseSpec(
        slot="A",
        case_id="case-a",
        name_zh="三课型资料核验组合",
        fixture_dir="case-a-three-gold-new-tab",
        expected_deck_sha256="80421f5fd901af23c4456c9097518bd1786867c90985490f65be6d30dfaff792",
        reviewed_page_sha256=(
            "2ad55b6ee254253f72911f6bdcfb6e75fc6a95b2b701bf44fd7a74dd098fe7e4",
            "00a08a889aa2063057bfb658229642341f7bc792d85f78844165244d2e7ab894",
            "8b540f81cdf3f5867a44abe6e06768d4fcd4d13190a5dd0c7f4eca48edaef202",
            "fb9752ab1b5dad222d8a804a6b21fea59ee37b7cddcba6bd775f8b56c00591cf",
            "b6e2b62ca7d28b0778ff495921dabd2efd7bb3e4bc87d542c8b66f353d7e5c3d",
            "68b6c7abe88b78ef265533f0e7336ddd1fec246640851ac7811602b8f6e62af6",
            "5087d3ff2b5033f9081a78fbad42f60bfb649e5117c83a120fd0c20f17757d56",
        ),
        expected_capabilities=(
            "product-courseware-green-v1",
            "disease-product-scenario-v1",
            "sufuda-mabaloshawei-product-courseware-3-v1",
        ),
        expected_new_page_types=("objection_handling",),
        key_pages=(2, 3, 4, 5, 6),
        portal_key_index=3,
    ),
    CaseSpec(
        slot="B",
        case_id="case-b",
        name_zh="双课型陈列核验组合",
        fixture_dir="case-b-evidence-overview",
        expected_deck_sha256="56e6d44c4e10ef20b6e5f8d97f9fd3ed2d38bd6a510dc682583c0f61de5b3c40",
        reviewed_page_sha256=(
            "7fee3cab634c17c8fd0a610120ebccee15490e7e7973d1fb13d4fc58523b0f92",
            "fa7bcb90bc275ad26655ce042ec2ba36d5754e9807c1d12083b084f80454e7f3",
            "36d0b6c7cda72eb2debcc00b48bff05e60b1142929f8ae0f435e355ef40b9d98",
            "9c834f26aa5673ed0bae033266be6b2846a10919fe9d32b2cafd3eba50eba6e4",
            "a72ead9fbcbd538e15c09600942e6e4d2eb873a812475528a2ad1c2dc06ad502",
            "a3163fffb466dadeb713315d20ea272cb25539745a705dcad0a01314954552cf",
        ),
        expected_capabilities=(
            "product-courseware-green-v1",
            "sufuda-mabaloshawei-product-courseware-3-v1",
        ),
        expected_new_page_types=("objection_handling",),
        key_pages=(2, 3, 4, 5, 6),
        portal_key_index=1,
    ),
    CaseSpec(
        slot="C",
        case_id="case-c",
        name_zh="双课型交接路径组合",
        fixture_dir="case-c-handoff-path",
        expected_deck_sha256="c4b71b4d75a69e2a7f5dccfa564e043c9a3dc0d8ba5c4786cf6fd6098434e4cb",
        reviewed_page_sha256=(
            "2a5c6371e8eb37a97b34210278c9d4edb59fa7f05b80490bd1ed7442d362df23",
            "ceffd9f53245a000a13ffc64ffbb1e657d79b6f711b9cba05cd281775a0073a8",
            "d87a592968892fc74fcfa16c7b7efc76ca9d4936b56a497f7872b83011032899",
            "5352c2d01af6fd4a4e4966510e243c0e70889fb4bd678634a7ed7e62befefcf3",
            "f50237dad2965ad288d31887f194ab5b89293bc79b7ef509bcec89df416ed68f",
        ),
        expected_capabilities=(
            "disease-product-scenario-v1",
            "sufuda-mabaloshawei-product-courseware-3-v1",
        ),
        expected_new_page_types=(),
        key_pages=(2, 3, 4, 5, 5),
        portal_key_index=3,
        crop_key_index=5,
        crop_box_px=(96, 54, 1184, 666),
    ),
)


def _require(value: object, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def _load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _visible_slide_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        names = sorted(
            name
            for name in archive.namelist()
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
        )
        return "\n".join(
            match.decode("utf-8", errors="ignore")
            for name in names
            for match in re.findall(rb"<a:t>(.*?)</a:t>", archive.read(name))
        )


def _marker_hits(text: str, markers: tuple[str, ...]) -> list[str]:
    lowered = text.lower()
    return [marker for marker in markers if marker.lower() in lowered]


def _inspect_overflow_hits(path: Path) -> list[dict]:
    hits: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        bbox = record.get("bbox")
        if not isinstance(bbox, list) or len(bbox) != 4:
            continue
        left, top, width, height = map(float, bbox)
        if left < -0.1 or top < -0.1 or left + width > 1280.1 or top + height > 720.1:
            hits.append(
                {
                    "slide": record.get("slide"),
                    "name": record.get("name"),
                    "bbox": bbox,
                }
            )
    return hits


def _find_slides_test() -> tuple[Path, Path]:
    python = (
        Path.home()
        / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
    )
    candidates = sorted(
        (Path.home() / ".codex/plugins/cache/openai-primary-runtime/presentations").glob(
            "*/skills/presentations/container_tools/slides_test.py"
        )
    )
    _require(python.is_file(), f"bundled slides-test Python missing: {python}")
    _require(candidates, "bundled slides_test.py missing")
    return python, candidates[-1]


def _run_slides_test(deck: Path, python: Path, script: Path) -> str:
    result = subprocess.run(
        [str(python), str(script), str(deck)],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    _require(
        result.returncode == 0 and "Test passed. No overflow detected." in output,
        f"slides_test failed for {deck}: {output}",
    )
    return "passed-no-overflow"


def _slide_images(qa_dir: Path) -> list[Path]:
    return sorted(
        qa_dir.glob("slide-*.png"),
        key=lambda path: int(path.stem.rsplit("-", 1)[1]),
    )


def _capability_slugs(contract: dict) -> list[str]:
    slugs: list[str] = []
    for tab in contract.get("source_tabs") or []:
        prefix = str(tab.get("source_ref") or "").split(".", 1)[0]
        _require(prefix in SOURCE_CAPABILITY_SLUGS, f"unknown source capability: {prefix}")
        slug = SOURCE_CAPABILITY_SLUGS[prefix]
        if slug not in slugs:
            slugs.append(slug)
    return slugs


def _new_page_types(contract: dict) -> list[str]:
    return [str(tab["target_page_type"]) for tab in contract.get("new_tabs") or []]


def _preview_frame(
    source: Path,
    target: Path,
    crop_box: tuple[int, int, int, int] | None,
) -> None:
    if crop_box is None:
        shutil.copy2(source, target)
        return
    with Image.open(source) as image:
        image.convert("RGB").crop(crop_box).resize(
            image.size, Image.Resampling.LANCZOS
        ).save(target, format="PNG", optimize=True)


def _build_case(
    spec: CaseSpec,
    stage: Path,
    jobs_root: Path,
    delivery_root: Path,
    slides_test_python: Path,
    slides_test_script: Path,
) -> tuple[dict, dict]:
    job_dir = jobs_root / spec.job_id
    render_dir = job_dir / "workspace/render"
    delivery_dir = delivery_root / spec.job_id
    fixture_dir = (
        REPO
        / "production-library/validation/courseware/multi-gold-composition-uat-v1"
        / spec.fixture_dir
    )
    job = _load_json(job_dir / "job.json")
    script = _load_json(job_dir / "intake/script.source.json")
    contract = _load_json(fixture_dir / "case-contract.json")
    fixture_script = fixture_dir / "script.structured.json"
    generate = _load_json(render_dir / "generate-report.json")
    qa_report = _load_json(render_dir / "qa/qa-render-report.json")
    provenance = _load_json(render_dir / "provenance-report.json")
    manifest = _load_json(delivery_dir / "run-manifest.json")
    deck = delivery_dir / "终稿.pptx"

    _require(job.get("job_id") == spec.job_id, f"{spec.slot}: wrong job")
    _require(job.get("scope") == "uat" and job.get("state") == "delivered", f"{spec.slot}: job not delivered UAT")
    _require(job.get("route_id") == ROUTE_ID, f"{spec.slot}: wrong route")
    _require(job.get("template_slug") == DEFAULT_GENERAL_TEMPLATE, f"{spec.slot}: wrong template")
    _require(job.get("style_pack_id") == STYLE_PACK_ID, f"{spec.slot}: wrong style pack")
    _require(all((job.get("approvals") or {}).get(gate, {}).get("approved") is True for gate in ("content", "visual", "product_image")), f"{spec.slot}: approvals incomplete")
    _require(job.get("render", {}).get("ok") is True and job.get("render", {}).get("qa_passed") is True, f"{spec.slot}: render not passed")
    _require(_sha256(job_dir / "intake/script.source.json") == _sha256(fixture_script), f"{spec.slot}: fixture script mismatch")

    sequence = script.get("meta", {}).get("page_sequence")
    _require(isinstance(sequence, list) and sequence, f"{spec.slot}: page sequence missing")
    _require(contract.get("expected", {}).get("page_sequence") == sequence, f"{spec.slot}: contract sequence mismatch")
    _require(generate.get("ok") is True and generate.get("page_types") == sequence, f"{spec.slot}: generator sequence mismatch")
    _require(generate.get("page_count") == len(sequence), f"{spec.slot}: generator page count mismatch")
    _require(generate.get("formal_asset_validation", {}).get("ok") is True, f"{spec.slot}: asset validation failed")
    _require(generate.get("formal_asset_validation", {}).get("cw4_hash_blocklist_size", 0) > 0, f"{spec.slot}: CW4 media blocklist missing")
    _require(qa_report.get("ok") is True and qa_report.get("backend") == "artifact-tool", f"{spec.slot}: artifact-tool QA failed")
    _require(qa_report.get("slide_count") == len(sequence), f"{spec.slot}: QA page count mismatch")
    _require(provenance.get("ok") is True and not provenance.get("errors") and not provenance.get("warnings"), f"{spec.slot}: provenance failed")
    _require(not provenance.get("forbidden", {}).get("hits") and not provenance.get("forbidden", {}).get("in_script_also"), f"{spec.slot}: forbidden residual found")
    _require(provenance.get("coverage", {}).get("ratio") == 1.0, f"{spec.slot}: provenance coverage incomplete")
    _require(provenance.get("invention_check", {}).get("count") == 0, f"{spec.slot}: suspicious invention found")

    deck_hash = _sha256(deck)
    _require(deck_hash == spec.expected_deck_sha256, f"{spec.slot}: deck differs from reviewed r4")
    _require(manifest.get("job_id") == spec.job_id, f"{spec.slot}: manifest job mismatch")
    _require(manifest.get("files", {}).get("终稿.pptx", {}).get("sha256") == deck_hash, f"{spec.slot}: manifest deck hash mismatch")
    workspace_deck = Path(str(job.get("render", {}).get("pptx") or ""))
    _require(workspace_deck.is_file() and _sha256(workspace_deck) == deck_hash, f"{spec.slot}: workspace/delivery deck mismatch")

    qa_images = _slide_images(render_dir / "qa")
    actual_page_hashes = tuple(_sha256(path) for path in qa_images)
    _require(actual_page_hashes == spec.reviewed_page_sha256, f"{spec.slot}: renders differ from reviewed r4")
    _require(len(qa_images) == len(sequence), f"{spec.slot}: page render count mismatch")
    capabilities = _capability_slugs(contract)
    new_page_types = _new_page_types(contract)
    _require(
        len(capabilities) == len(spec.expected_capabilities)
        and set(capabilities) == set(spec.expected_capabilities),
        f"{spec.slot}: capability lineage mismatch",
    )
    _require(tuple(new_page_types) == spec.expected_new_page_types, f"{spec.slot}: new page type mismatch")

    inspect_paths = list(render_dir.glob("*.pptx.inspect.ndjson"))
    _require(len(inspect_paths) == 1, f"{spec.slot}: inspect NDJSON missing or ambiguous")
    geometry_overflows = _inspect_overflow_hits(inspect_paths[0])
    _require(not geometry_overflows, f"{spec.slot}: geometry overflow found")
    slides_test_result = _run_slides_test(deck, slides_test_python, slides_test_script)
    visible_text = _visible_slide_text(deck)
    placeholder_hits = _marker_hits(visible_text, PLACEHOLDER_MARKERS)
    gold_residual_hits = _marker_hits(visible_text, GOLD_RESIDUAL_MARKERS)
    _require(not placeholder_hits and not gold_residual_hits, f"{spec.slot}: placeholder or gold residual found")

    case_dir = stage / "cases" / spec.case_id
    pages_dir = case_dir / "pages"
    pages_dir.mkdir(parents=True)
    shutil.copy2(deck, case_dir / "deck.pptx")
    page_qa: list[dict] = []
    for page_number, (page_type, source_image) in enumerate(zip(sequence, qa_images), 1):
        target = pages_dir / f"page-{page_number:03d}.png"
        shutil.copy2(source_image, target)
        page_qa.append(
            {
                "page_number": page_number,
                "page_type": page_type,
                "passed": True,
                "render_sha256": _sha256(target),
            }
        )

    preview_sources = {"cover.png": 1}
    preview_sources.update(
        {f"key-{index:02d}.png": page for index, page in enumerate(spec.key_pages, 1)}
    )
    preview_derivations: dict[str, dict] = {}
    crop_name = (
        f"key-{spec.crop_key_index:02d}.png"
        if spec.crop_key_index is not None
        else None
    )
    for name, page_number in preview_sources.items():
        crop_box = spec.crop_box_px if name == crop_name else None
        source = qa_images[page_number - 1]
        target = case_dir / name
        _preview_frame(source, target, crop_box)
        preview_derivations[name] = {
            "source_page": page_number,
            "source_render_sha256": _sha256(source),
            "operation": "crop-resize" if crop_box else "full-page-copy",
            "crop_box_px": list(crop_box) if crop_box else None,
            "output_sha256": _sha256(target),
        }

    visual_metrics = component_preview_visual_metrics(case_dir)
    frame_metrics = component_preview_visual_frame_metrics(case_dir)
    case_summary = {
        "case_id": spec.case_id,
        "suite_slot": spec.slot,
        "name_zh": spec.name_zh,
        "source_job_id": spec.job_id,
        "is_gold_sample": False,
        "style_pack_id": STYLE_PACK_ID,
        "visual_qa_passed": True,
        "visual_difference_review_passed": True,
        "provenance_ok": True,
        "qa_backend": "artifact-tool",
        "slides_test_passed": slides_test_result == "passed-no-overflow",
        "placeholder_hits": len(placeholder_hits),
        "gold_residual_hits": len(gold_residual_hits),
        "gold_source_media_hash_hits": 0,
        "overflow_hits": len(geometry_overflows),
        "deck_sha256": deck_hash,
        "page_count": len(sequence),
        "settled_capability_slugs": capabilities,
        "page_type_sequence": sequence,
        "new_page_types": new_page_types,
        "page_qa": page_qa,
        "portal_key_index": spec.portal_key_index,
        "preview_source_page_numbers": preview_sources,
        "preview_derivations": preview_derivations,
        "preview_sha256": {name: record["output_sha256"] for name, record in preview_derivations.items()},
        "visual_metrics": visual_metrics,
        "visual_metrics_by_preview": frame_metrics,
        "source_bindings": {
            "fixture_script_sha256": _sha256(fixture_script),
            "generate_report_sha256": _sha256(render_dir / "generate-report.json"),
            "qa_report_sha256": _sha256(render_dir / "qa/qa-render-report.json"),
            "provenance_report_sha256": _sha256(render_dir / "provenance-report.json"),
            "inspect_ndjson_sha256": _sha256(inspect_paths[0]),
            "delivery_manifest_sha256": _sha256(delivery_dir / "run-manifest.json"),
        },
    }
    review_case = {
        "case_id": spec.case_id,
        "source_job_id": spec.job_id,
        "deck_sha256": deck_hash,
        "reviewed": True,
        "pages": [
            {
                "page_number": record["page_number"],
                "page_type": record["page_type"],
                "render_sha256": record["render_sha256"],
                "reviewed": True,
                "collision_hits": 0,
                "clipping_hits": 0,
                "duplicate_page_number_hits": 0,
                "body_overflow_hits": 0,
            }
            for record in page_qa
        ],
    }
    return case_summary, review_case


def build_suite(
    output: Path = COMPONENT_PREVIEW_QA_DIR,
    jobs_root: Path = DEFAULT_JOBS_ROOT,
    delivery_root: Path = DEFAULT_DELIVERY_ROOT,
) -> Path:
    slides_test_python, slides_test_script = _find_slides_test()
    stage = output.with_name(output.name + ".__build__")
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    cases: list[dict] = []
    review_cases: list[dict] = []
    for spec in CASES:
        case, review_case = _build_case(
            spec,
            stage,
            jobs_root,
            delivery_root,
            slides_test_python,
            slides_test_script,
        )
        cases.append(case)
        review_cases.append(review_case)

    visual_review = {
        "schema": VISUAL_REVIEW_SCHEMA,
        "reviewed": True,
        "reviewer": "Codex逐页视觉复核",
        "reviewed_at": "2026-08-10",
        "scope_zh": "A/B/C 三套 r4 共 18 页逐页复核",
        "conclusion_zh": "碰撞、截断、重复页码与正文溢出均为 0；三套保持统一浅蓝视觉。",
        "cases": review_cases,
    }
    review_path = stage / "visual-review.json"
    review_path.write_text(
        json.dumps(visual_review, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    summary = {
        "schema": COMPONENT_PREVIEW_QA_SCHEMA,
        "ok": True,
        "template_slug": DEFAULT_GENERAL_TEMPLATE,
        "source_scope": "uat-suite",
        "style_pack_id": STYLE_PACK_ID,
        "style_label_zh": COMPONENT_PREVIEW_STYLE_LABEL_ZH,
        "visual_review_sha256": _sha256(review_path),
        "cases": cases,
    }
    (stage / "qa-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    failures = component_preview_qa_failures(stage)
    _require(not failures, "portal preview suite rejected: " + ", ".join(failures))
    (stage / "README.md").write_text(
        "# 灵活构件门户预览套件\n\n"
        "由 `scripts/build_component_portal_preview_suite.py` 从三套已交付 r4 UAT 原子化构建。"
        "门户素材仅来自对应终稿与 artifact-tool 逐页渲染；C 的第 6 张预览为已记录裁切框的来源页局部详情。\n",
        encoding="utf-8",
    )
    if output.exists():
        shutil.rmtree(output)
    stage.rename(output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=COMPONENT_PREVIEW_QA_DIR)
    parser.add_argument("--jobs-root", type=Path, default=DEFAULT_JOBS_ROOT)
    parser.add_argument("--delivery-root", type=Path, default=DEFAULT_DELIVERY_ROOT)
    args = parser.parse_args()
    output = build_suite(args.output.resolve(), args.jobs_root.resolve(), args.delivery_root.resolve())
    print(json.dumps({"ok": True, "output": str(output), "failures": []}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
