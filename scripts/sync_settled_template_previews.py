#!/usr/bin/env python3
"""Materialize production-quality preview/ for every settled template.

Source frames come from signed samples / settled canonicals. The flexible component
fallback is the exception: its portal preview may switch only to a qualified,
non-gold UAT snapshot. Does not invent demo artwork.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import zipfile
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

REPO = Path(__file__).resolve().parents[1]
SETTLED = REPO / "production-library/templates/settled"
VAL = REPO / "production-library/validation"
GS = VAL / "courseware/gold-samples"
GUIDES = REPO / "assets/business-input-guides"
ROUTES_PATH = REPO / "production-library/business-routes.json"
DEFAULT_GENERAL_TEMPLATE = "product-courseware-component-v1"
COMPONENT_PREVIEW_QA_SCHEMA = "component-portal-preview-suite-qa-v3"
COMPONENT_PREVIEW_QA_DIR = (
    VAL
    / "courseware"
    / "product-courseware-component-flexible-uat-v1"
    / "portal-preview"
)
COMPONENT_PREVIEW_KEY_LABELS = (
    "封面",
    "痛点与数据",
    "核心功效",
    "产品特点",
    "适宜人群",
)
COURSEWARE4_STYLE_PACK_ID = "style-pack.courseware-4-silk-yellow-red-v1"
COURSEWARE4_GOLD_PREVIEW_DIR = (
    VAL
    / "courseware"
    / "product-courseware-4-faithful-replica-v1"
    / "out"
    / "engine-v1-gold-qa"
)
COMPONENT_PREVIEW_MAX_COURSEWARE4_BACKGROUND_RATIO = 0.20
COMPONENT_PREVIEW_MAX_TOP_YELLOW_RED_RATIO = 0.01
COMPONENT_PREVIEW_MAX_GOLD_LAYOUT_SIMILARITY = 0.75
COMPONENT_PREVIEW_MAX_CROSS_CASE_KEY_LAYOUT_SIMILARITY = 0.90
COMPONENT_PREVIEW_MIN_CASES = 3
COMPONENT_PREVIEW_REQUIRED_SLOT_MIN_PAGES = {"A": 7, "B": 6, "C": 5}
COMPONENT_PREVIEW_STYLE_LABEL_ZH = "统一浅蓝商品培训视觉"
SIGNED_STANDARD_TEMPLATES = frozenset(
    {
        "product-courseware-green-v1",
        "disease-product-scenario-v1",
        "sufuda-mabaloshawei-product-courseware-3-v1",
        "kangaisen-lycopene-health-edu-v1",
    }
)
SETTLED_CAPABILITY_LABELS = {
    "product-courseware-green-v1": "绿色商品培训 5 页",
    "disease-product-scenario-v1": "疾病 + 商品场景 18 页",
    "sufuda-mabaloshawei-product-courseware-3-v1": "商品培训课件3 13 页",
    "kangaisen-lycopene-health-edu-v1": "成分健康科普 20 页",
}


def _component_preview_paths(qa_dir: Path) -> list[Path]:
    return [
        qa_dir / "cover.png",
        *(qa_dir / f"key-{index:02d}.png" for index in range(1, 6)),
    ]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _courseware4_background_ratio(path: Path) -> float:
    image = Image.open(path).convert("RGB").resize((160, 90))
    pixels = list(image.getdata())
    # The settled courseware-4 canvas is approximately rgb(207, 204, 197).
    hits = sum(
        1
        for red, green, blue in pixels
        if abs(red - 207) <= 10
        and abs(green - 204) <= 10
        and abs(blue - 197) <= 10
    )
    return hits / len(pixels)


def _top_yellow_red_ratio(path: Path) -> float:
    image = Image.open(path).convert("RGB").resize((160, 90))
    pixels = image.load()
    hits = 0
    total = 160 * 30
    for y in range(30):
        for x in range(160):
            red, green, blue = pixels[x, y]
            silk_yellow = (
                red >= 180
                and green >= 140
                and blue <= 120
                and red - blue >= 70
                and green - blue >= 40
            )
            # Courseware-4 uses a dark brick red. Keep the detector narrow so the
            # flexible blue style's coral status accent is not treated as that identity.
            silk_red = (
                red >= 130
                and green <= 100
                and blue <= 100
                and red - green >= 45
                and red - blue >= 40
            )
            if silk_yellow or silk_red:
                hits += 1
    return hits / total


def _edge_grid_signature(path: Path) -> list[float]:
    image = (
        Image.open(path)
        .convert("L")
        .resize((160, 90))
        .filter(ImageFilter.FIND_EDGES)
    )
    values: list[float] = []
    for row in range(9):
        for column in range(16):
            cell = image.crop(
                (column * 10, row * 10, (column + 1) * 10, (row + 1) * 10)
            )
            values.append(sum(cell.getdata()) / (255 * 100))
    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0:
        return values
    return [value / norm for value in values]


def _strong_edge_mask(path: Path) -> Image.Image:
    edge = (
        Image.open(path)
        .convert("L")
        .resize((160, 90))
        .filter(ImageFilter.FIND_EDGES)
    )
    return edge.point(lambda value: 255 if value >= 36 else 0)


def _edge_mask_count(mask: Image.Image) -> int:
    return sum(mask.histogram()[1:])


def _edge_mask_similarity(left: Image.Image, right: Image.Image) -> float:
    """Compare actual strong-edge positions with one-pixel anti-alias tolerance."""
    left_dilated = left.filter(ImageFilter.MaxFilter(3))
    right_dilated = right.filter(ImageFilter.MaxFilter(3))
    left_count = _edge_mask_count(left)
    right_count = _edge_mask_count(right)
    left_precision = _edge_mask_count(
        ImageChops.multiply(left, right_dilated)
    ) / max(left_count, 1)
    right_precision = _edge_mask_count(
        ImageChops.multiply(right, left_dilated)
    ) / max(right_count, 1)
    return (
        2 * left_precision * right_precision / (left_precision + right_precision)
        if left_precision + right_precision
        else 0.0
    )


def component_preview_visual_frame_metrics(
    qa_dir: Path = COMPONENT_PREVIEW_QA_DIR,
) -> dict[str, dict[str, float | str | bool]]:
    """Return auditable per-frame identity metrics and nearest courseware-4 page."""
    previews = _component_preview_paths(qa_dir)
    gold_paths = sorted(COURSEWARE4_GOLD_PREVIEW_DIR.glob("slide-*.png"))
    if not gold_paths:
        raise FileNotFoundError(COURSEWARE4_GOLD_PREVIEW_DIR)
    gold_hashes = {_sha256(path): path.name for path in gold_paths}
    gold_masks = [_strong_edge_mask(path) for path in gold_paths]
    out: dict[str, dict[str, float | str | bool]] = {}
    for path in previews:
        preview_mask = _strong_edge_mask(path)
        similarities = [
            _edge_mask_similarity(preview_mask, gold_mask)
            for gold_mask in gold_masks
        ]
        nearest_index = max(range(len(similarities)), key=similarities.__getitem__)
        preview_hash = _sha256(path)
        out[path.name] = {
            "courseware4_preview_exact_hash_match": preview_hash in gold_hashes,
            "courseware4_background_ratio": _courseware4_background_ratio(path),
            "top_courseware4_yellow_red_ratio": _top_yellow_red_ratio(path),
            "gold_layout_similarity": similarities[nearest_index],
            "nearest_courseware4_page": gold_paths[nearest_index].name,
        }
    return out


def component_preview_visual_metrics(
    qa_dir: Path = COMPONENT_PREVIEW_QA_DIR,
) -> dict[str, float | int]:
    """Measure direct visual overlap with the courseware-4 preview identity."""
    frame_metrics = component_preview_visual_frame_metrics(qa_dir)
    return {
        "courseware4_preview_exact_hash_hits": sum(
            metric["courseware4_preview_exact_hash_match"] is True
            for metric in frame_metrics.values()
        ),
        "max_courseware4_background_ratio": max(
            float(metric["courseware4_background_ratio"])
            for metric in frame_metrics.values()
        ),
        "max_top_yellow_red_ratio": max(
            float(metric["top_courseware4_yellow_red_ratio"])
            for metric in frame_metrics.values()
        ),
        "max_gold_layout_similarity": max(
            float(metric["gold_layout_similarity"])
            for metric in frame_metrics.values()
        ),
    }


def _valid_sha256(value: object) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _is_pptx(path: Path) -> bool:
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
    except (OSError, zipfile.BadZipFile):
        return False
    return {"[Content_Types].xml", "ppt/presentation.xml"}.issubset(names)


def _load_component_preview_summary(qa_dir: Path) -> dict | None:
    summary_path = qa_dir / "qa-summary.json"
    if not summary_path.is_file():
        return None
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return summary if isinstance(summary, dict) else None


def _max_pairwise_layout_similarity(paths: list[Path]) -> float:
    signatures = [_edge_grid_signature(path) for path in paths]
    return max(
        (
            sum(a * b for a, b in zip(signatures[left], signatures[right]))
            for left in range(len(signatures))
            for right in range(left + 1, len(signatures))
        ),
        default=0.0,
    )


def component_preview_qa_failures(
    qa_dir: Path = COMPONENT_PREVIEW_QA_DIR,
) -> list[str]:
    """Return stable reason codes for every suite preview promotion gate."""
    summary_path = qa_dir / "qa-summary.json"
    if not summary_path.is_file():
        return ["qa_summary_missing"]
    summary = _load_component_preview_summary(qa_dir)
    if summary is None:
        return ["qa_summary_invalid"]

    checks = (
        (summary.get("schema") == COMPONENT_PREVIEW_QA_SCHEMA, "qa_schema_v3_required"),
        (summary.get("ok") is True, "qa_not_passed"),
        (summary.get("template_slug") == DEFAULT_GENERAL_TEMPLATE, "wrong_template"),
        (summary.get("source_scope") == "uat-suite", "not_uat_suite_scope"),
        (
            summary.get("style_label_zh") == COMPONENT_PREVIEW_STYLE_LABEL_ZH,
            "style_label_mismatch",
        ),
    )
    failures = [reason for passed, reason in checks if not passed]
    review_path = qa_dir / "visual-review.json"
    review_cases_by_id: dict[str, dict] = {}
    if not review_path.is_file():
        failures.append("visual_review_missing")
    elif (
        not _valid_sha256(summary.get("visual_review_sha256"))
        or _sha256(review_path) != summary.get("visual_review_sha256")
    ):
        failures.append("visual_review_hash_binding_mismatch")
    else:
        try:
            visual_review = json.loads(review_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            visual_review = None
        if not isinstance(visual_review, dict):
            failures.append("visual_review_invalid")
        elif (
            visual_review.get("schema")
            != "component-portal-preview-visual-review-v1"
            or visual_review.get("reviewed") is not True
            or visual_review.get("reviewer") != "Codex逐页视觉复核"
            or not isinstance(visual_review.get("cases"), list)
        ):
            failures.append("visual_review_not_passed")
        else:
            review_cases_by_id = {
                str(item.get("case_id")): item
                for item in visual_review["cases"]
                if isinstance(item, dict) and item.get("case_id")
            }
    suite_style_pack_id = summary.get("style_pack_id")
    if not isinstance(suite_style_pack_id, str) or not suite_style_pack_id.strip():
        failures.append("style_pack_missing")
    elif suite_style_pack_id == COURSEWARE4_STYLE_PACK_ID:
        failures.append("courseware4_style_pack_forbidden")

    cases = summary.get("cases")
    if not isinstance(cases, list):
        failures.append("suite_cases_missing")
        return failures
    if len(cases) < COMPONENT_PREVIEW_MIN_CASES:
        failures.append("suite_case_count_too_small")

    case_ids: list[str] = []
    case_slots: list[str] = []
    source_job_ids: list[str] = []
    deck_hashes: list[str] = []
    page_type_sequences: list[tuple[str, ...]] = []
    settled_capabilities: set[str] = set()
    new_page_types: set[str] = set()
    all_preview_hashes: list[str] = []
    representative_paths: list[Path] = []

    for position, case in enumerate(cases, 1):
        if not isinstance(case, dict):
            failures.append(f"case:{position}:invalid")
            continue
        case_id = str(case.get("case_id") or "")
        prefix = f"case:{case_id or position}:"
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,63}", case_id):
            failures.append(prefix + "case_id_invalid")
            continue
        case_ids.append(case_id)
        case_dir = qa_dir / "cases" / case_id

        suite_slot = str(case.get("suite_slot") or "")
        if not re.fullmatch(r"[A-Z]", suite_slot):
            failures.append(prefix + "suite_slot_invalid")
        else:
            case_slots.append(suite_slot)
        name_zh = case.get("name_zh")
        if not isinstance(name_zh, str) or not name_zh.strip():
            failures.append(prefix + "name_missing")
        source_job_id = str(case.get("source_job_id") or "")
        source_job_ids.append(source_job_id)
        if not source_job_id.startswith("uat-"):
            failures.append(prefix + "source_job_not_uat")
        if case.get("is_gold_sample") is not False:
            failures.append(prefix + "gold_sample_forbidden")
        if case.get("style_pack_id") != suite_style_pack_id:
            failures.append(prefix + "mixed_style_pack")
        if case.get("visual_qa_passed") is not True:
            failures.append(prefix + "visual_qa_not_passed")
        if case.get("visual_difference_review_passed") is not True:
            failures.append(prefix + "visual_difference_not_reviewed")
        if case.get("provenance_ok") is not True:
            failures.append(prefix + "provenance_not_passed")
        if case.get("qa_backend") != "artifact-tool":
            failures.append(prefix + "artifact_tool_qa_required")
        if case.get("slides_test_passed") is not True:
            failures.append(prefix + "slides_test_not_passed")
        for field, reason in (
            ("placeholder_hits", "placeholder_hits"),
            ("gold_residual_hits", "gold_residual_hits"),
            ("gold_source_media_hash_hits", "gold_source_media_hash_hits"),
            ("overflow_hits", "overflow_hits"),
        ):
            if case.get(field) != 0:
                failures.append(prefix + reason)

        sequence_value = case.get("page_type_sequence")
        sequence = (
            tuple(sequence_value)
            if isinstance(sequence_value, list)
            and sequence_value
            and all(isinstance(item, str) and item.strip() for item in sequence_value)
            else ()
        )
        if not sequence:
            failures.append(prefix + "page_type_sequence_missing")
        else:
            page_type_sequences.append(sequence)
        if case.get("page_count") != len(sequence):
            failures.append(prefix + "page_count_mismatch")
        slot_minimum = COMPONENT_PREVIEW_REQUIRED_SLOT_MIN_PAGES.get(suite_slot, 5)
        if len(sequence) < slot_minimum:
            failures.append(prefix + "formal_deck_page_count_too_small")

        capability_value = case.get("settled_capability_slugs")
        capabilities = (
            capability_value
            if isinstance(capability_value, list)
            and capability_value
            and len(capability_value) == len(set(capability_value))
            and all(isinstance(item, str) for item in capability_value)
            else []
        )
        if not capabilities:
            failures.append(prefix + "settled_capabilities_missing")
        elif not set(capabilities).issubset(SETTLED_CAPABILITY_LABELS):
            failures.append(prefix + "unknown_settled_capability")
        else:
            settled_capabilities.update(capabilities)

        new_value = case.get("new_page_types")
        case_new_page_types = (
            new_value
            if isinstance(new_value, list)
            and len(new_value) == len(set(new_value))
            and all(isinstance(item, str) and item.strip() for item in new_value)
            else None
        )
        if case_new_page_types is None:
            failures.append(prefix + "new_page_types_invalid")
        elif not set(case_new_page_types).issubset(sequence):
            failures.append(prefix + "new_page_type_not_in_sequence")
        else:
            new_page_types.update(case_new_page_types)

        deck_path = case_dir / "deck.pptx"
        deck_sha256 = case.get("deck_sha256")
        if not deck_path.is_file():
            failures.append(prefix + "source_deck_missing")
        elif not _is_pptx(deck_path):
            failures.append(prefix + "source_deck_invalid")
        elif not _valid_sha256(deck_sha256) or _sha256(deck_path) != deck_sha256:
            failures.append(prefix + "source_deck_hash_binding_mismatch")
        else:
            deck_hashes.append(deck_sha256)

        page_qa = case.get("page_qa")
        if not isinstance(page_qa, list) or len(page_qa) != len(sequence):
            failures.append(prefix + "page_qa_incomplete")
        else:
            page_qa_failed = False
            page_render_missing = False
            page_render_hash_mismatch = False
            for page_number, (page_type, record) in enumerate(
                zip(sequence, page_qa), 1
            ):
                if (
                    not isinstance(record, dict)
                    or record.get("page_number") != page_number
                    or record.get("page_type") != page_type
                    or record.get("passed") is not True
                    or not _valid_sha256(record.get("render_sha256"))
                ):
                    page_qa_failed = True
                    continue
                render_path = case_dir / "pages" / f"page-{page_number:03d}.png"
                if not render_path.is_file():
                    page_render_missing = True
                elif _sha256(render_path) != record["render_sha256"]:
                    page_render_hash_mismatch = True
            if page_qa_failed:
                failures.append(prefix + "page_qa_not_passed")
            if page_render_missing:
                failures.append(prefix + "page_render_missing")
            if page_render_hash_mismatch:
                failures.append(prefix + "page_render_hash_binding_mismatch")

        review_case = review_cases_by_id.get(case_id)
        review_pages = review_case.get("pages") if isinstance(review_case, dict) else None
        if (
            not isinstance(review_case, dict)
            or review_case.get("reviewed") is not True
            or review_case.get("deck_sha256") != deck_sha256
            or not isinstance(review_pages, list)
            or not isinstance(page_qa, list)
            or len(review_pages) != len(page_qa)
            or any(
                not isinstance(review_page, dict)
                or review_page.get("reviewed") is not True
                or review_page.get("page_number") != page_record.get("page_number")
                or review_page.get("page_type") != page_record.get("page_type")
                or review_page.get("render_sha256")
                != page_record.get("render_sha256")
                or any(
                    review_page.get(field) != 0
                    for field in (
                        "collision_hits",
                        "clipping_hits",
                        "duplicate_page_number_hits",
                        "body_overflow_hits",
                    )
                )
                for review_page, page_record in zip(review_pages, page_qa)
                if isinstance(page_record, dict)
            )
        ):
            failures.append(prefix + "visual_review_binding_mismatch")

        previews = _component_preview_paths(case_dir)
        if not all(path.is_file() for path in previews):
            failures.append(prefix + "preview_files_missing")
            continue
        actual_hashes = {path.name: _sha256(path) for path in previews}
        if case.get("preview_sha256") != actual_hashes:
            failures.append(prefix + "preview_hash_binding_mismatch")
        if len(set(actual_hashes.values())) != len(previews):
            failures.append(prefix + "duplicate_preview_frames")
        all_preview_hashes.extend(actual_hashes.values())

        preview_source_pages = case.get("preview_source_page_numbers")
        if (
            not isinstance(preview_source_pages, dict)
            or set(preview_source_pages) != set(actual_hashes)
            or not all(
                isinstance(page_number, int)
                and 1 <= page_number <= len(sequence)
                for page_number in preview_source_pages.values()
            )
        ):
            failures.append(prefix + "preview_source_pages_invalid")
        elif len(set(preview_source_pages.values())) < 3:
            failures.append(prefix + "preview_source_pages_too_narrow")

        portal_key_index = case.get("portal_key_index")
        if not isinstance(portal_key_index, int) or not 1 <= portal_key_index <= 5:
            failures.append(prefix + "portal_key_index_invalid")
        else:
            representative_paths.append(case_dir / f"key-{portal_key_index:02d}.png")

        try:
            metrics = component_preview_visual_metrics(case_dir)
        except (OSError, ValueError):
            failures.append(prefix + "preview_visual_metrics_failed")
            continue
        if metrics["courseware4_preview_exact_hash_hits"] != 0:
            failures.append(prefix + "courseware4_preview_hash_hit")
        if (
            metrics["max_courseware4_background_ratio"]
            > COMPONENT_PREVIEW_MAX_COURSEWARE4_BACKGROUND_RATIO
        ):
            failures.append(prefix + "courseware4_background_ratio_too_high")
        if (
            metrics["max_top_yellow_red_ratio"]
            > COMPONENT_PREVIEW_MAX_TOP_YELLOW_RED_RATIO
        ):
            failures.append(prefix + "courseware4_yellow_red_ratio_too_high")
        if (
            metrics["max_gold_layout_similarity"]
            > COMPONENT_PREVIEW_MAX_GOLD_LAYOUT_SIMILARITY
        ):
            failures.append(prefix + "courseware4_layout_similarity_too_high")

    if len(case_ids) != len(set(case_ids)):
        failures.append("duplicate_case_id")
    if len(case_slots) != len(cases) or len(case_slots) != len(set(case_slots)):
        failures.append("duplicate_or_invalid_suite_slot")
    if not set(COMPONENT_PREVIEW_REQUIRED_SLOT_MIN_PAGES).issubset(case_slots):
        failures.append("required_suite_slots_missing")
    if len(source_job_ids) != len(cases) or len(source_job_ids) != len(
        set(source_job_ids)
    ):
        failures.append("duplicate_source_job_id")
    if len(deck_hashes) != len(cases) or len(deck_hashes) != len(set(deck_hashes)):
        failures.append("duplicate_or_unbound_source_deck")
    if len(page_type_sequences) != len(cases) or len(page_type_sequences) != len(
        set(page_type_sequences)
    ):
        failures.append("page_type_sequences_not_unique")
    if not 2 <= len(settled_capabilities) <= 3:
        failures.append("suite_settled_capability_count_invalid")
    if not new_page_types:
        failures.append("suite_new_page_type_missing")
    if len(all_preview_hashes) != len(set(all_preview_hashes)):
        failures.append("duplicate_preview_frames_across_suite")
    if (
        len(representative_paths) == len(cases)
        and len(cases) >= COMPONENT_PREVIEW_MIN_CASES
    ):
        try:
            if (
                _max_pairwise_layout_similarity(representative_paths)
                > COMPONENT_PREVIEW_MAX_CROSS_CASE_KEY_LAYOUT_SIMILARITY
            ):
                failures.append("cross_case_key_layout_similarity_too_high")
        except (OSError, ValueError):
            failures.append("cross_case_visual_metrics_failed")
    return failures


def qualified_component_preview_sources(
    qa_dir: Path = COMPONENT_PREVIEW_QA_DIR,
) -> tuple[Path, list[tuple[Path, str]]] | None:
    """Return one distinct representative from every qualified UAT case."""
    if component_preview_qa_failures(qa_dir):
        return None
    summary = _load_component_preview_summary(qa_dir)
    if summary is None:
        return None
    cases = summary["cases"]
    cover = qa_dir / "cases" / cases[0]["case_id"] / "cover.png"
    keys = [
        (
            qa_dir
            / "cases"
            / case["case_id"]
            / f"key-{case['portal_key_index']:02d}.png",
            f"{case['name_zh']} · 差异化关键页",
        )
        for case in cases
    ]
    return cover, keys


def component_preview_suite_evidence(
    qa_dir: Path = COMPONENT_PREVIEW_QA_DIR,
) -> dict | None:
    """Return machine evidence for a fully qualified UAT suite."""
    if component_preview_qa_failures(qa_dir):
        return None
    summary = _load_component_preview_summary(qa_dir)
    if summary is None:
        return None
    capability_slugs: list[str] = []
    new_page_types: list[str] = []
    cases: list[dict] = []
    for media_index, case in enumerate(summary["cases"], 1):
        for slug in case["settled_capability_slugs"]:
            if slug not in capability_slugs:
                capability_slugs.append(slug)
        for page_type in case["new_page_types"]:
            if page_type not in new_page_types:
                new_page_types.append(page_type)
        representative_page_number = case["preview_source_page_numbers"][
            f"key-{case['portal_key_index']:02d}.png"
        ]
        cases.append(
            {
                "case_id": case["case_id"],
                "suite_slot": case["suite_slot"],
                "name_zh": case["name_zh"],
                "source_job_id": case["source_job_id"],
                "page_count": case["page_count"],
                "source_capability_labels_zh": [
                    SETTLED_CAPABILITY_LABELS[slug]
                    for slug in case["settled_capability_slugs"]
                ],
                "page_type_sequence": case["page_type_sequence"],
                "new_page_types": case["new_page_types"],
                "representative_page_number": representative_page_number,
                "representative_page_type": case["page_type_sequence"][
                    representative_page_number - 1
                ],
                "portal_media_index": media_index,
            }
        )
    return {
        "schema": COMPONENT_PREVIEW_QA_SCHEMA,
        "case_count": len(cases),
        "style_pack_id": summary["style_pack_id"],
        "style_label_zh": summary["style_label_zh"],
        "settled_capability_labels_zh": [
            SETTLED_CAPABILITY_LABELS[slug] for slug in capability_slugs
        ],
        "new_page_types": new_page_types,
        "cases": cases,
    }


_LEGACY_COMPONENT_PREVIEW_COVER = (
    VAL
    / "courseware/product-courseware-4-faithful-replica-v1"
    / "out/engine-v1-gold-qa/slide-01.png"
)
_LEGACY_COMPONENT_PREVIEW_KEYS = [
    (
        VAL
        / "courseware/product-courseware-4-faithful-replica-v1"
        / f"out/engine-v1-gold-qa/slide-{slide}.png",
        label,
    )
    for slide, label in zip(
        ("01", "02", "03", "06", "09"), COMPONENT_PREVIEW_KEY_LABELS
    )
]
_qualified_component_preview = qualified_component_preview_sources()
COMPONENT_PREVIEW_SUITE_EVIDENCE = component_preview_suite_evidence()
COMPONENT_PREVIEW_IDENTITY_QUALIFIED = _qualified_component_preview is not None
COMPONENT_PREVIEW_IDENTITY_NOTE_ZH = (
    "至少 3 套正式差异化非金样 UAT 已通过逐页 QA、来源、页型组合、色彩、构图与文件哈希门闸。"
    if COMPONENT_PREVIEW_IDENTITY_QUALIFIED
    else "至少 3 套正式差异化非金样 UAT suite 尚未通过 QA；为避免误认成课件4，门户暂不展示旧图。"
)
if _qualified_component_preview is None:
    COMPONENT_PREVIEW_COVER = _LEGACY_COMPONENT_PREVIEW_COVER
    COMPONENT_PREVIEW_KEYS = _LEGACY_COMPONENT_PREVIEW_KEYS
else:
    COMPONENT_PREVIEW_COVER, COMPONENT_PREVIEW_KEYS = _qualified_component_preview
COMPONENT_PREVIEW_KEY_LIMIT = len(COMPONENT_PREVIEW_KEYS)


def capability_matrix(
    *,
    content_draft: bool,
    new_theme_preview: bool,
    new_theme_pptx: bool,
    new_theme_mp4: bool,
    business_selfserve: bool = False,
) -> dict[str, bool]:
    """Static workflow support; runtime capability is checked on the business machine."""
    return {
        "gold_viewable": True,
        "content_draft": content_draft,
        "new_theme_preview": new_theme_preview,
        "new_theme_pptx": new_theme_pptx,
        "new_theme_mp4": new_theme_mp4,
        "business_selfserve": business_selfserve,
    }


def load_routes_by_template(path: Path = ROUTES_PATH) -> dict[str, list[dict]]:
    """Load route truth without exposing route IDs in the business catalog."""
    if not path.is_file():
        return {}
    doc = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, list[dict]] = {}
    for route in doc.get("routes") or []:
        slug = route.get("template_slug")
        if slug:
            out.setdefault(str(slug), []).append(route)
    return out


def route_deliverables(route: dict) -> list[str]:
    deliverable = str(route.get("deliverable") or "")
    if deliverable == "pptx_and_mp4":
        return ["pptx", "mp4"]
    return [deliverable] if deliverable in {"pptx", "mp4"} else []


def shelf_group_for_slug(slug: str) -> str:
    if slug == DEFAULT_GENERAL_TEMPLATE:
        return "default-general"
    if slug in SIGNED_STANDARD_TEMPLATES:
        return "signed-standard"
    return "other"


def derive_catalog_entry(
    source: dict,
    routes_by_template: dict[str, list[dict]],
) -> dict:
    """Derive executable capabilities from active routes, never handwritten flags."""
    entry = dict(source)
    slug = str(entry["slug"])
    configured_routes = routes_by_template.get(slug) or []
    active_routes = [route for route in configured_routes if route.get("active")]
    deliverables = {
        deliverable
        for route in active_routes
        for deliverable in route_deliverables(route)
    }
    capabilities = dict(entry.get("capabilities") or {})
    capabilities.update(
        {
            "content_draft": bool(active_routes),
            "new_theme_preview": bool(active_routes),
            "new_theme_pptx": "pptx" in deliverables,
            "new_theme_mp4": "mp4" in deliverables,
            "business_selfserve": bool(active_routes),
        }
    )
    entry["capabilities"] = capabilities
    entry["shelf_group"] = shelf_group_for_slug(slug)
    if active_routes:
        route_outputs: list[str] = []
        if "pptx" in deliverables:
            route_outputs.append("可编辑 PPTX")
        if "mp4" in deliverables:
            route_outputs.append("MP4 培训视频")
        if route_outputs:
            entry["outputs"] = route_outputs
        output_label = " / ".join(
            label for deliverable, label in (("pptx", "PPTX"), ("mp4", "MP4"))
            if deliverable in deliverables
        ) or "正式成品"
        prefix = (
            "灵活构件兜底"
            if slug == DEFAULT_GENERAL_TEMPLATE
            else "已签样标准课型"
            if slug in SIGNED_STANDARD_TEMPLATES
            else "正式路线"
        )
        entry["status_label"] = f"{prefix} · {output_label} 可生成"
        entry["status_note"] = (
            "先整理内容初稿与素材清单；内容、所需授权素材和视觉确认全部通过后，"
            "由 WorkBuddy 生成正式成品并完成逐页质量检查。"
        )
        if slug == DEFAULT_GENERAL_TEMPLATE:
            entry["status_note"] += (
                " 旧 12 页仅为结构冒烟，不是金样；业务预览与能力验收以 A/B/C 非金样套件为准。"
            )
        entry["blockers"] = []
    elif configured_routes or slug in SIGNED_STANDARD_TEMPLATES:
        entry["status_label"] = "尚未开放 · 当前不可生成 · 金样可查看"
        entry["status_note"] = (
            "金样、结构和填写参考可以复用；正式换主题生产路线尚未激活，不承诺生成正式成品。"
        )
        entry["blockers"] = ["正式换主题生产路线尚未激活"]
    return entry


# Business-facing catalog (Chinese names only for shelf)
CATALOG: list[dict] = [
    {
        "slug": "health-video-reference-tech-v1",
        "name_zh": "疾病科普视频（如风热证）",
        "one_liner": "健康知识讲解视频：症状 · 机理 · 治疗与用药建议",
        "gallery_title_zh": "疾病科普视频 · 风热证金样",
        "outputs": ["MP4 培训视频"],
        "category": "疾病科普",
        "capabilities": capability_matrix(
            content_draft=True,
            new_theme_preview=True,
            new_theme_pptx=False,
            new_theme_mp4=True,
        ),
        "requirements": ["药师/法务审核稿", "已批准主题包", "video_full", "正式 voice_id"],
        "blockers": ["正式出片前必须完成主题画面审批", "当前机器须通过 video_full 环境检查"],
        "status_label": "可开始草稿 · 正式出片需环境与审批",
        "status_note": "金样可查看；换病种先整理审核稿与主题包，内容和画面确认后，且本机 video_full 通过才生成正式 MP4。",
        "cover_src": GS / "wind-heat-video-gold-v1/web/media/cover-product.jpg",
        "keys": [
            (GS / "wind-heat-video-gold-v1/web/media/thumbs/cover.jpg", "开场"),
            (GS / "wind-heat-video-gold-v1/web/media/thumbs/symptoms.jpg", "典型症状"),
            (GS / "wind-heat-video-gold-v1/web/media/thumbs/mechanism.jpg", "病因机理"),
            (GS / "wind-heat-video-gold-v1/web/media/thumbs/treatment.jpg", "治疗思路"),
            (GS / "wind-heat-video-gold-v1/web/media/thumbs/medication.jpg", "用药建议"),
            (GS / "wind-heat-video-gold-v1/web/media/thumbs/summary.jpg", "总结"),
        ],
        "fallback_keys": [
            (GUIDES / "settled-template-frames/health-template-reference-005s.png", "母版角色"),
            (GUIDES / "settled-template-frames/health-template-reference-018s.png", "症状页"),
            (GUIDES / "settled-template-frames/health-template-reference-026s.png", "机理页"),
            (GUIDES / "final-video-frames/health-wind-heat-003s-intro.png", "开场帧"),
            (GUIDES / "final-video-frames/health-wind-heat-021s-mechanism.png", "机理帧"),
            (GUIDES / "final-video-frames/health-wind-heat-052s-treatment.png", "治疗帧"),
        ],
        "voice_id": "voice.reference-pharmacist-qwen-v1",
    },
    {
        "slug": "product-video-faithful-v1",
        "name_zh": "商品培训视频（如辅酶 Q10）",
        "one_liner": "单品店员培训视频：介绍 · 功效 · 证据 · 人群 · 联合 · 总结",
        "gallery_title_zh": "商品培训视频 · 辅酶 Q10 金样",
        "outputs": ["MP4 培训视频"],
        "category": "商品培训",
        "capabilities": capability_matrix(
            content_draft=True,
            new_theme_preview=True,
            new_theme_pptx=False,
            new_theme_mp4=True,
        ),
        "requirements": ["完整 8 段审核稿", "公司授权包装图与凭证", "哈希绑定审批", "video_full", "正式 voice_id"],
        "blockers": ["内容/包装/授权凭证未完成哈希审批时只能生成草稿预览", "当前机器须通过 video_full 环境检查"],
        "status_label": "可开始草稿 · 审批与环境通过后出片",
        "status_note": "金样可查看；业务先确认完整 8 段脚本、分镜、包装图和授权凭证，哈希审批匹配且本机 video_full 通过后才生成正式 MP4。",
        "cover_src": GS / "product-q10-video-gold-v1/web/media/cover-product.png",
        "keys": [
            (GS / "product-q10-video-gold-v1/web/media/thumbs/opening.jpg", "开场"),
            (GS / "product-q10-video-gold-v1/web/media/thumbs/brand.jpg", "品牌/品类"),
            (GS / "product-q10-video-gold-v1/web/media/thumbs/efficacy.jpg", "核心功效"),
            (GS / "product-q10-video-gold-v1/web/media/thumbs/features.jpg", "产品特点"),
            (GS / "product-q10-video-gold-v1/web/media/thumbs/audience.jpg", "适宜人群"),
            (GS / "product-q10-video-gold-v1/web/media/thumbs/combo.jpg", "联合用药"),
        ],
        "fallback_keys": [
            (GUIDES / "settled-template-frames/product-template-reference-pair01.png", "讲师页"),
            (GUIDES / "settled-template-frames/product-template-reference-pair04.png", "图文讲解"),
            (GUIDES / "settled-template-frames/product-template-reference-pair06.png", "包装主视觉"),
            (GUIDES / "final-video-frames/product-q10-007s-overview.png", "概览"),
            (GUIDES / "final-video-frames/product-q10-015s-efficacy.png", "功效"),
            (GUIDES / "final-video-frames/product-q10-025s-evidence.png", "证据"),
        ],
        "voice_id": "voice.reference-pharmacist-qwen-v1",
    },
    {
        "slug": "product-courseware-component-v1",
        "name_zh": "灵活构件商品培训 PPT（兜底）",
        "one_liner": "未命中 5/18/13/20 页固定课型时使用；按审核大纲动态编排",
        "gallery_title_zh": "灵活构件商品培训 · 兜底路线",
        "outputs": ["可编辑 PPTX"],
        "category": "商品培训",
        "capabilities": capability_matrix(
            content_draft=True,
            new_theme_preview=True,
            new_theme_pptx=True,
            new_theme_mp4=False,
        ),
        "requirements": [
            "内容初稿确认",
            "业务授权正式包装图",
            "素材计划全部就绪",
            "完整逐页视觉 QA",
            "pptx_export",
        ],
        "blockers": [],
        "status_label": "灵活构件兜底 · 确认后生成可编辑 PPTX",
        "status_note": "先审内容与素材计划，完成正式图绑定和逐页视觉 QA 后交付可编辑 PPTX。",
        "capabilities_note_zh": (
            "gold_viewable 为旧兼容键，仅表示 A/B/C 非金样预览可查看；"
            "旧 12 页结构冒烟稿不是金样。"
        ),
        "preview_identity_qualified": COMPONENT_PREVIEW_IDENTITY_QUALIFIED,
        "preview_identity_note_zh": COMPONENT_PREVIEW_IDENTITY_NOTE_ZH,
        "preview_suite_evidence": COMPONENT_PREVIEW_SUITE_EVIDENCE,
        "preview_key_limit": COMPONENT_PREVIEW_KEY_LIMIT,
        "cover_src": COMPONENT_PREVIEW_COVER,
        "keys": COMPONENT_PREVIEW_KEYS,
        "fallback_keys": [],
        "voice_id": None,
    },
    {
        "slug": "product-courseware-green-v1",
        "name_zh": "绿色单品 PPT（如金银花露）",
        "one_liner": "五页绿色商品培训：介绍/卖点/人群 · 联合用药 · 对标 · 注意",
        "gallery_title_zh": "绿色商品培训 · 5 页",
        "outputs": ["可编辑 PPTX"],
        "category": "商品培训",
        "capabilities": capability_matrix(
            content_draft=True,
            new_theme_preview=True,
            new_theme_pptx=True,
            new_theme_mp4=False,
        ),
        "requirements": [
            "完整 5 页审核稿",
            "本品/搭档/竞品授权图片",
            "4 张正式注意事项插图",
            "内容/商品图/视觉确认",
            "pptx_export",
        ],
        "blockers": [],
        "status_label": "可开始草稿 · 确认后生成 PPTX",
        "status_note": "五页绿色金样可查看；先整理内容初稿与缺口，业务确认后且本机 pptx_export 通过再生成可编辑 PPTX。",
        "cover_src": GS / "jinyinhualu-pptx-gold-v1/web/media/cover-product.png",
        "keys": [
            (GS / "jinyinhualu-pptx-gold-v1/web/media/slides/slide-01.png", "封面/介绍"),
            (GS / "jinyinhualu-pptx-gold-v1/web/media/slides/slide-02.png", "卖点与人群"),
            (GS / "jinyinhualu-pptx-gold-v1/web/media/slides/slide-03.png", "联合用药"),
            (GS / "jinyinhualu-pptx-gold-v1/web/media/slides/slide-04.png", "品种对标"),
            (GS / "jinyinhualu-pptx-gold-v1/web/media/slides/slide-05.png", "注意事项"),
        ],
        "fallback_keys": [
            (GUIDES / "courseware-template-slides/honeysuckle-template-slide-01.png", "页 1"),
            (GUIDES / "courseware-template-slides/honeysuckle-template-slide-02.png", "页 2"),
            (GUIDES / "courseware-template-slides/honeysuckle-template-slide-03.png", "页 3"),
        ],
        "voice_id": None,
    },
    {
        "slug": "disease-product-scenario-v1",
        "name_zh": "疾病+商品场景 PPT（如穿心莲）",
        "one_liner": "辨证知识 + 商品知识 + 销售场景的可编辑长课件",
        "gallery_title_zh": "疾病辨证与商品场景 · 穿心莲金样",
        "outputs": ["可编辑 PPTX"],
        "category": "商品培训",
        "capabilities": capability_matrix(
            content_draft=True,
            new_theme_preview=True,
            new_theme_pptx=True,
            new_theme_mp4=False,
        ),
        "requirements": [
            "完整 18 页审核稿",
            "疾病/商品/两组场景/权重商品字段",
            "全部正式图片",
            "内容/商品图/视觉确认",
            "pptx_export",
        ],
        "blockers": [],
        "status_label": "已签样标准课型 · PPTX 可生成",
        "status_note": "先审完整 18 页内容与图片，三道确认通过后生成可编辑 PPTX。",
        "cover_src": GS / "chuanxinlian-pptx-gold-v1/web/media/cover-product.png",
        "keys": [
            (GS / "chuanxinlian-pptx-gold-v1/web/media/slides/slide-01.png", "封面"),
            (GS / "chuanxinlian-pptx-gold-v1/web/media/slides/slide-03.png", "辨证/知识"),
            (GS / "chuanxinlian-pptx-gold-v1/web/media/slides/slide-09.png", "商品知识"),
            (GS / "chuanxinlian-pptx-gold-v1/web/media/slides/slide-14.png", "销售场景"),
            (GS / "chuanxinlian-pptx-gold-v1/web/media/slides/slide-18.png", "收尾页"),
        ],
        "fallback_keys": [
            (GUIDES / "courseware-template-slides/andrographolide-template-slide-01.png", "页 1"),
            (GUIDES / "courseware-template-slides/andrographolide-template-slide-09.png", "页 9"),
            (GUIDES / "courseware-template-slides/andrographolide-template-slide-14.png", "页 14"),
        ],
        "voice_id": None,
    },
    {
        "slug": "sufuda-mabaloshawei-product-courseware-3-v1",
        "name_zh": "商品培训课件3（可编辑 PPT，速福达标准课型）",
        "one_liner": "复用速福达金样的 12 个内容单元，生成 13 页新主题可编辑 PPTX",
        "gallery_title_zh": "商品培训课件3 · 速福达金样",
        "outputs": ["可编辑 PPTX"],
        "category": "商品培训",
        "capabilities": capability_matrix(
            content_draft=True,
            new_theme_preview=True,
            new_theme_pptx=True,
            new_theme_mp4=False,
        ),
        "requirements": [
            "12 个主题内容单元（导出为 13 页 PPTX）",
            "6 类业务授权包装/Logo",
            "23 个主题插图显式绑定",
            "内容/商品图/视觉确认",
            "pptx_export",
        ],
        "blockers": [],
        "status_label": "已签样标准课型 · PPTX 可生成",
        "status_note": "PPTX 已接入；MP4 是独立路线，完整视频环境与 QA 未通过前不承诺生成。",
        "cover_src": VAL
        / "courseware/sufuda-product-courseware-3-gold-v1/web/media/cover-product.png",
        "keys": [
            (
                VAL / "courseware/sufuda-product-courseware-3-gold-v1/web/media/t-cover.png",
                "封面",
            ),
            (
                VAL / "courseware/sufuda-product-courseware-3-gold-v1/web/media/t-flu.png",
                "流感背景",
            ),
            (
                VAL / "courseware/sufuda-product-courseware-3-gold-v1/web/media/t-benefit.png",
                "核心利益",
            ),
            (
                VAL / "courseware/sufuda-product-courseware-3-gold-v1/web/media/t-feature.png",
                "产品特点",
            ),
            (
                VAL / "courseware/sufuda-product-courseware-3-gold-v1/web/media/t-audience.png",
                "适宜人群",
            ),
            (
                VAL / "courseware/sufuda-product-courseware-3-gold-v1/web/media/t-combo.png",
                "联合用药",
            ),
        ],
        "fallback_keys": [
            (
                VAL
                / "courseware/sufuda-product-courseware-3-gold-v1/web/media/pptx-slides/slide-01.png",
                "PPT 封面",
            ),
            (
                VAL
                / "courseware/sufuda-product-courseware-3-gold-v1/web/media/pptx-slides/slide-04.png",
                "PPT 卖点",
            ),
            (
                VAL
                / "courseware/sufuda-product-courseware-3-gold-v1/web/media/pptx-slides/slide-08.png",
                "PPT 人群",
            ),
            (
                VAL
                / "courseware/sufuda-product-courseware-3-gold-v1/web/media/pptx-slides/slide-10.png",
                "PPT 联合",
            ),
        ],
        "voice_id": "voice.sufuda-courseware-pharmacist-v1",
    },
    {
        "template_id": "template.kangaisen-lycopene-health-edu-v1",
        "slug": "kangaisen-lycopene-health-edu-v1",
        "name_zh": "番茄红素成分健康科普 PPT（米白番茄红）",
        "one_liner": "20 页成分健康科普：定义与来源、抗氧化机制、健康研究、吸收指南与应用；独立米白番茄红课型，不是福尔课件4",
        "gallery_title_zh": "番茄红素成分健康科普 · 20 页米白番茄红金样",
        "outputs": ["可编辑 PPTX"],
        "category": "成分健康科普",
        "capabilities": capability_matrix(
            content_draft=False,
            new_theme_preview=False,
            new_theme_pptx=False,
            new_theme_mp4=False,
        ),
        "requirements": [
            "完整 20 页成分健康科普审核稿",
            "成分定义/来源/机制/研究/补充指南字段",
            "药师与合规终审",
            "全部正式图片及版权/授权",
            "内容/素材/视觉确认",
            "pptx_export",
        ],
        "blockers": ["正式换主题生产路线尚未激活"],
        "status_label": "尚未开放 · 当前不可生成 · 金样可查看",
        "status_note": "独立 20 页成分健康科普框架，不是福尔商品培训课件4；当前先查看金样与整理审核内容，生产路线激活后再生成 PPTX。",
        "cover_src": VAL
        / "courseware/kangaisen-lycopene-health-edu-v1/preview/cover.jpg",
        "keys": [
            (
                VAL
                / "courseware/kangaisen-lycopene-health-edu-v1/preview/key-01.jpg",
                "成分定义",
            ),
            (
                VAL
                / "courseware/kangaisen-lycopene-health-edu-v1/preview/key-02.jpg",
                "抗氧化能力",
            ),
            (
                VAL
                / "courseware/kangaisen-lycopene-health-edu-v1/preview/key-03.jpg",
                "健康研究",
            ),
            (
                VAL
                / "courseware/kangaisen-lycopene-health-edu-v1/preview/key-04.jpg",
                "吸收指南",
            ),
            (
                VAL
                / "courseware/kangaisen-lycopene-health-edu-v1/preview/key-05.jpg",
                "目录结构",
            ),
        ],
        "fallback_keys": [
            (
                VAL
                / "courseware/kangaisen-lycopene-health-edu-v1/out/qa-gold/slide-04.jpg",
                "成分定义",
            ),
            (
                VAL
                / "courseware/kangaisen-lycopene-health-edu-v1/out/qa-gold/slide-08.jpg",
                "抗氧化能力",
            ),
            (
                VAL
                / "courseware/kangaisen-lycopene-health-edu-v1/out/qa-gold/slide-11.jpg",
                "健康研究",
            ),
            (
                VAL
                / "courseware/kangaisen-lycopene-health-edu-v1/out/qa-gold/slide-15.jpg",
                "吸收指南",
            ),
            (
                VAL
                / "courseware/kangaisen-lycopene-health-edu-v1/out/qa-gold/slide-02.jpg",
                "目录结构",
            ),
        ],
        "voice_id": None,
    },
    {
        "slug": "fuler-fanqiehongsu-product-courseware-4-v1",
        "name_zh": "商品培训课件4（视频+PPT，番茄红素壳）",
        "one_liner": "保健品培训：全片视频 + 16 页可编辑 PPT（关联用药/总结行标题语法）",
        "gallery_title_zh": "商品培训课件4 · 福尔番茄红素金样",
        "outputs": ["MP4", "可编辑 PPTX"],
        "category": "商品培训",
        "capabilities": capability_matrix(
            content_draft=True,
            new_theme_preview=False,
            new_theme_pptx=False,
            new_theme_mp4=False,
        ),
        "requirements": ["courseware4 换主题 adapter"],
        "blockers": ["课件4换主题 CLI 尚未接线；当前仅提供金样预览"],
        "status_label": "仅金样预览 · 换主题入口待接线",
        "status_note": "金样 v2 MP4/PPTX 可查看；当前换主题 CLI 未接线，不承诺生成新主题正式成品。",
        "cover_src": VAL
        / "courseware/product-courseware-4-faithful-replica-v1/web/media/cover-product.png",
        "keys": [
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/stills/S00_cover.png",
                "封面",
            ),
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/stills/S03_product_intro.png",
                "商品介绍",
            ),
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/stills/S04_benefit_1.png",
                "利益点",
            ),
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/stills/S10_audience.png",
                "适宜人群",
            ),
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/stills/S12_related_1.png",
                "关联用药",
            ),
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/stills/S11_summary.png",
                "总结",
            ),
        ],
        "fallback_keys": [
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/pptx-slides/slide-01.png",
                "PPT 1",
            ),
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/pptx-slides/slide-05.png",
                "PPT 5",
            ),
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/pptx-slides/slide-12.png",
                "PPT 12",
            ),
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/thumbs/01.png",
                "缩略 1",
            ),
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/thumbs/04.png",
                "缩略 4",
            ),
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/thumbs/08.png",
                "缩略 8",
            ),
        ],
        "voice_id": "voice.sufuda-courseware-pharmacist-v1",
    },
    {
        "slug": "disease-health-shenke-blue-v1",
        "name_zh": "疾病健康知识培训 PPT（参课蓝）",
        "one_liner": "门店健康顾问疾病知识培训：概览、表现、检查、用药、关怀、一页通",
        "gallery_title_zh": "疾病健康知识培训 · 参课蓝金样",
        "outputs": ["可编辑 PPTX"],
        "category": "健康培训",
        "capabilities": capability_matrix(
            content_draft=True,
            new_theme_preview=False,
            new_theme_pptx=False,
            new_theme_mp4=False,
        ),
        "requirements": ["医学审核稿", "疾病课件统一业务 adapter"],
        "blockers": ["换病种生成尚未接入统一业务入口"],
        "status_label": "金样可查看 · 换病种入口待接线",
        "status_note": "参课蓝 v3 金样可查看；当前可先整理审核内容，不承诺业务自助生成新病种正式 PPTX。",
        "cover_src": GS / "uri-shenke-health-pptx-gold-v1/web/media/cover-product.png",
        "keys": [
            (GS / "uri-shenke-health-pptx-gold-v1/web/media/slides/slide-02.png", "疾病概览"),
            (GS / "uri-shenke-health-pptx-gold-v1/web/media/slides/slide-03.png", "临床表现"),
            (GS / "uri-shenke-health-pptx-gold-v1/web/media/slides/slide-09.png", "对症用药表"),
            (GS / "uri-shenke-health-pptx-gold-v1/web/media/slides/slide-14.png", "专业关怀"),
            (GS / "uri-shenke-health-pptx-gold-v1/web/media/slides/slide-18.png", "竖版一页通"),
        ],
        "fallback_keys": [
            # validation 媒体可能被 gitignore；settled 内 preview 作回退源
            (
                SETTLED / "disease-health-shenke-blue-v1/preview/cover.png",
                "封面",
            ),
            (
                SETTLED / "disease-health-shenke-blue-v1/preview/key-01.png",
                "疾病概览",
            ),
            (
                SETTLED / "disease-health-shenke-blue-v1/preview/key-02.png",
                "临床表现",
            ),
            (
                SETTLED / "disease-health-shenke-blue-v1/preview/key-03.png",
                "对症用药表",
            ),
            (
                SETTLED / "disease-health-shenke-blue-v1/preview/key-04.png",
                "专业关怀",
            ),
            (
                SETTLED / "disease-health-shenke-blue-v1/preview/key-05.png",
                "竖版一页通",
            ),
        ],
        "voice_id": None,
    },
]


def ensure_rgb_png(src: Path, dest: Path, max_w: int = 1600) -> None:
    """Copy/convert to PNG; downscale only if wider than max_w (keep quality)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        if im.mode in ("RGBA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[-1] if im.mode == "RGBA" else None)
            im = bg
        elif im.mode != "RGB":
            im = im.convert("RGB")
        if im.width > max_w:
            ratio = max_w / im.width
            im = im.resize((max_w, max(1, int(im.height * ratio))), Image.Resampling.LANCZOS)
        im.save(dest, "PNG", optimize=True)


def _settled_preview_keys(root: Path, limit: int) -> list[tuple[Path, str]]:
    preview_dir = root / "preview"
    paths = sorted(preview_dir.glob("key-*.png"))[:limit]
    if not paths:
        return []
    labels: list[str] = []
    manifest_path = root / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            labels = list((manifest.get("preview") or {}).get("key_frame_labels_zh") or [])
        except (OSError, json.JSONDecodeError, TypeError):
            labels = []
    return [
        (path, labels[index] if index < len(labels) else f"关键页 {index + 1}")
        for index, path in enumerate(paths)
    ]


def pick_keys(entry: dict, settled_root: Path | None = None) -> list[tuple[Path, str]]:
    limit = max(3, int(entry.get("preview_key_limit") or 6))
    chosen: list[tuple[Path, str]] = []
    for path, label in entry["keys"]:
        if path.is_file():
            chosen.append((path, label))
    if len(chosen) < 3:
        for path, label in entry.get("fallback_keys") or []:
            if path.is_file() and path not in {p for p, _ in chosen}:
                chosen.append((path, label))
            if len(chosen) >= limit:
                break
    if settled_root is not None:
        existing = _settled_preview_keys(settled_root, limit)
        # The committed settled preview is the approved production source.  A dirty
        # maker workspace may contain newer validation renders with the same count;
        # letting those silently win makes business-package rebuilds differ from a
        # clean clone.  Source/fallback frames are only for bootstrapping a template
        # that does not yet have a complete settled preview.
        if len(existing) >= 3:
            chosen = existing
    return chosen[:limit]


def update_manifest(slug: str, entry: dict, key_files: list[str], key_labels: list[str]) -> None:
    manifest_path = SETTLED / slug / "manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    capabilities = entry["capabilities"]
    production_ready = bool(capabilities["business_selfserve"])
    data["preview"] = {
        "cover": "preview/cover.png",
        "key_frames": key_files,
        "key_frame_labels_zh": key_labels,
        "gallery_title_zh": entry["gallery_title_zh"],
        "one_liner": entry["one_liner"],
        "name_zh": entry["name_zh"],
        "category_zh": entry["category"],
        "outputs": entry["outputs"],
        "capabilities": capabilities,
        "requirements": entry["requirements"],
        "blockers": entry["blockers"],
        "production_ready": production_ready,
        "status_label": entry["status_label"],
        "status_note": entry["status_note"],
        "capabilities_note_zh": entry.get("capabilities_note_zh"),
        "shelf_group": entry["shelf_group"],
        "preview_identity_qualified": bool(
            entry.get("preview_identity_qualified", True)
        ),
        "preview_identity_note_zh": entry.get("preview_identity_note_zh"),
        "preview_suite_evidence": entry.get("preview_suite_evidence"),
        "online_url": None,
    }
    data["business_catalog"] = {
        "name_zh": entry["name_zh"],
        "one_liner": entry["one_liner"],
        "blank_word": "业务提交_空白模板.docx",
        "filled_example": "业务提交_填写参考.docx",
        "framework_guide": "../../框架填写说明.md",
        "shelf_group": entry["shelf_group"],
    }
    if entry.get("template_id"):
        data["business_catalog"]["template_id"] = entry["template_id"]
    if entry.get("voice_id"):
        data["voice"] = {
            "voice_id": entry["voice_id"],
            "engine": "Qwen3-TTS-local-clone",
            "pace_policy": "v5-smooth",
            "forbid_system_tts": True,
        }
        # Keep existing voice_pack_id if already set
        if "voice_pack_id" not in data:
            data["voice_pack_id"] = entry["voice_id"]
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def write_preview_readme(preview_dir: Path, entry: dict, labels: list[str]) -> None:
    source_note = (
        "来源：至少 3 套正式非金样 UAT suite；每套独立逐页 QA、deck/页面/预览哈希绑定，"
        "并通过非课件4视觉差异门闸。"
        if entry.get("preview_suite_evidence")
        else "来源：已签样金样/归档媒体，仅用于业务辨认课型；不得当新项目生产素材直接复用包装与 Logo 像素。"
    )
    lines = [
        f"# 预览 · {entry['name_zh']}",
        "",
        f"- 一句话：{entry['one_liner']}",
        f"- 状态：{entry['status_label']}",
        f"- 说明：{entry['status_note']}",
        "",
        "## 关键帧",
        "",
    ]
    for i, lab in enumerate(labels, 1):
        lines.append(f"- `key-{i:02d}.png` — {lab}")
    lines.extend(
        [
            "",
            source_note,
            "",
        ]
    )
    (preview_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    catalog_out: list[dict] = []
    routes_by_template = load_routes_by_template()
    for source_entry in CATALOG:
        entry = derive_catalog_entry(source_entry, routes_by_template)
        slug = entry["slug"]
        root = SETTLED / slug
        if not root.is_dir():
            raise SystemExit(f"missing settled template: {slug}")
        preview_dir = root / "preview"
        staged_preview = root / "preview.__sync__"
        if staged_preview.exists():
            shutil.rmtree(staged_preview)
        staged_preview.mkdir(parents=True)

        keys = pick_keys(entry, root)
        cover_src = entry["cover_src"]
        if not cover_src.is_file():
            settled_cover = preview_dir / "cover.png"
            if settled_cover.is_file():
                cover_src = settled_cover
            elif keys:
                cover_src = keys[0][0]
            else:
                raise SystemExit(f"no cover or keys for {slug}")
        ensure_rgb_png(cover_src, staged_preview / "cover.png")

        if len(keys) < 3:
            raise SystemExit(
                f"{slug}: need ≥3 key frames, got {len(keys)}: {[str(p) for p, _ in keys]}"
            )

        key_rel: list[str] = []
        key_labels: list[str] = []
        for i, (path, label) in enumerate(keys, 1):
            name = f"key-{i:02d}.png"
            ensure_rgb_png(path, staged_preview / name)
            key_rel.append(f"preview/{name}")
            key_labels.append(label)

        write_preview_readme(staged_preview, entry, key_labels)

        if preview_dir.exists():
            shutil.rmtree(preview_dir)
        staged_preview.rename(preview_dir)
        update_manifest(slug, entry, key_rel, key_labels)

        capabilities = entry["capabilities"]
        meta = {
            "slug": slug,
            "name_zh": entry["name_zh"],
            "one_liner": entry["one_liner"],
            "gallery_title_zh": entry["gallery_title_zh"],
            "outputs": entry["outputs"],
            "category": entry["category"],
            "capabilities": capabilities,
            "requirements": entry["requirements"],
            "blockers": entry["blockers"],
            "production_ready": bool(capabilities["business_selfserve"]),
            "status_label": entry["status_label"],
            "status_note": entry["status_note"],
            "capabilities_note_zh": entry.get("capabilities_note_zh"),
            "shelf_group": entry["shelf_group"],
            "preview_identity_qualified": bool(
                entry.get("preview_identity_qualified", True)
            ),
            "preview_identity_note_zh": entry.get("preview_identity_note_zh"),
            "preview_suite_evidence": entry.get("preview_suite_evidence"),
            "key_frame_labels_zh": key_labels,
            "voice_id": entry.get("voice_id"),
            "blank_word": "业务提交_空白模板.docx",
            "filled_example": "业务提交_填写参考.docx",
        }
        if entry.get("template_id"):
            meta["template_id"] = entry["template_id"]
        (preview_dir / "catalog-entry.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        catalog_out.append({**meta, "settled_dir": f"production-library/templates/settled/{slug}"})
        print(f"OK {slug}: cover + {len(keys)} keys")

    catalog_path = SETTLED / "business-catalog.json"
    catalog_path.write_text(
        json.dumps(
            {
                "version": "1.1.0",
                "updated": "2026-08-09",
                "purpose": "业务模板货架单一数据源；由 sync_settled_template_previews.py 生成",
                "templates": catalog_out,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {catalog_path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
