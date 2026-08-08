#!/usr/bin/env python3
"""PPTX 文案溯源 + 禁词表校验（M4.3）

规则：
1. 禁词表（默认：锌 / 硒 / 维生素E / 好物推荐）在 PPTX 正文中 0 命中
2. script 中的关键文案原子须在 PPTX 中出现（覆盖率）
3. PPTX 中较长正文不得明显脱离 script（防引擎/生成器扩写）

用法：
  python3 scripts/verify_text_provenance.py \\
    --pptx path/to/out.pptx \\
    --script path/to/script.structured.json \\
    --out path/to/provenance-report.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_FORBIDDEN = [
    "好物推荐",
    "维生素E",
    "维生素Ｅ",
]

# 单独字「锌」「硒」在商品名误伤风险：用词界/搭配
DEFAULT_FORBIDDEN_PATTERNS = [
    r"锌\s*/\s*硒",
    r"锌硒",
    r"(?<![a-zA-Z0-9])锌(?![a-zA-Z0-9])",
    r"(?<![a-zA-Z0-9])硒(?![a-zA-Z0-9])",
]

# 引擎 chrome / 占位 / 页码类，不计入「扩写」
CHROME_ALLOWLIST = {
    "待业务授权",
    "待业务替换",
    "图片占位",
    "可替换",
    "TIME",
    "Big",
    "Title",
    "BigTitle",
    "敲重点",
    "仅供内部学习",
    "不代替药物",
    "禁忌人群",
    "随餐服用",
    "就医咨询",
    "Sources",
    "content-model",
    "scene",
    "layer",
    "font",
    "engine",
    "courseware-pptx-v1",
    "generator_m4",
    "observed_reference",
    "business_extension",
    "HarmonyOS Sans SC",
    "Noto Sans SC",
    "Microsoft YaHei",
}

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(s: str) -> str:
    s = s.replace("\u3000", " ").replace("\xa0", " ")
    s = re.sub(r"\s+", "", s)
    return s.strip()


def extract_pptx_texts(pptx: Path) -> list[str]:
    """Extract visible text from slide XML (not notes by default — notes are engine meta)."""
    texts: list[str] = []
    with zipfile.ZipFile(pptx, "r") as zf:
        names = sorted(
            n
            for n in zf.namelist()
            if re.match(r"ppt/slides/slide\d+\.xml$", n)
        )
        for name in names:
            raw = zf.read(name)
            try:
                root = ET.fromstring(raw)
            except ET.ParseError:
                continue
            # a:t text runs
            for node in root.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}t"):
                if node.text and node.text.strip():
                    texts.append(node.text.strip())
    return texts


def visible_items(items: list | None) -> list:
    out = []
    for it in items or []:
        if isinstance(it, dict) and it.get("hidden"):
            continue
        out.append(it)
    return out


def script_atoms(script: dict) -> list[dict]:
    """Key copy atoms with roles for coverage check."""
    atoms: list[dict] = []

    def add(role: str, text: str, *, required: bool = True) -> None:
        t = (text or "").strip()
        if not t:
            return
        atoms.append({"role": role, "text": t, "required": required})

    meta = script.get("meta") or {}
    add("meta.display_name", meta.get("display_name", ""))
    add("meta.organization", meta.get("organization", ""), required=False)
    add("meta.tagline", meta.get("tagline", ""), required=False)

    hook = script.get("hook") or {}
    add("hook.title", hook.get("title", ""), required=False)
    # hook 全段文案可能被映射为 hook_pain_data（只保留症状/数据）；
    # 强制覆盖：数字指纹 + 白皮书/来源；整段 head 改为 soft（required=False）
    for i, p in enumerate(hook.get("paragraphs") or []):
        p = str(p).strip()
        if len(p) > 24:
            add(f"hook.paragraphs[{i}].head", p[:18], required=False)
            m = re.search(r"\d+(?:\.\d+)?%?", p)
            if m:
                add(f"hook.paragraphs[{i}].num", m.group(0), required=True)
        else:
            add(f"hook.paragraphs[{i}]", p, required=False)
    if re.search(r"白皮书|时代杂志", json.dumps(hook, ensure_ascii=False)):
        if "白皮书" in json.dumps(hook, ensure_ascii=False):
            add("hook.source_fingerprint", "白皮书", required=True)
        if "时代杂志" in json.dumps(hook, ensure_ascii=False):
            add("hook.time_fingerprint", "时代杂志", required=False)

    for key in ("benefits", "features"):
        block = script.get(key) or {}
        add(f"{key}.title", block.get("title", ""), required=False)
        for i, it in enumerate(visible_items(block.get("items"))):
            if isinstance(it, dict):
                add(f"{key}.items[{i}].title", it.get("title", ""))
                body = (it.get("body") or "").strip()
                if body:
                    add(f"{key}.items[{i}].body_head", body[:16], required=True)
            else:
                add(f"{key}.items[{i}]", str(it))

    aud = script.get("audience") or {}
    for i, it in enumerate(aud.get("items") or []):
        label = it if isinstance(it, str) else (it.get("label") or it.get("text") or "")
        add(f"audience.items[{i}]", str(label))

    combo = script.get("combination") or {}
    for i, r in enumerate(combo.get("rows") or []):
        add(f"combination.rows[{i}].partner", r.get("partner", ""))
        talk = (r.get("talk_track") or "").strip()
        if talk:
            add(f"combination.rows[{i}].talk_head", talk[:16])

    summary = script.get("summary") or {}
    for i, r in enumerate(summary.get("rows") or []):
        add(f"summary.rows[{i}].label", r.get("label", ""))
        val = (r.get("value") or r.get("body") or "").strip()
        if val:
            add(f"summary.rows[{i}].value_head", val[:12], required=False)

    prec = script.get("precautions") or {}
    for i, it in enumerate(prec.get("items") or []):
        text = it if isinstance(it, str) else (it.get("text") or "")
        text = str(text).strip()
        if text:
            add(f"precautions.items[{i}].head", text[:14])

    return atoms


def is_chrome(text: str) -> bool:
    t = text.strip()
    if not t:
        return True
    if t in CHROME_ALLOWLIST:
        return True
    if any(t == c or t in c or c in t for c in CHROME_ALLOWLIST if len(c) >= 2):
        # careful: only allow if text is short chrome-like
        if len(t) <= 12:
            return True
    # pure numbers / page indices
    if re.fullmatch(r"[\d./]+", t):
        return True
    if re.fullmatch(r"[+\-=×xX]+", t):
        return True
    # asset role keys leaked as alt/placeholder (snake_case / short tokens)
    if re.fullmatch(r"[a-z][a-z0-9_]{1,24}", t):
        return True
    if t in {"角标", "新疆地图", "软胶囊", "五个番茄", "原料实拍", "盒装A", "盒装B", "瓶装"}:
        return True
    # speaker-note-like technical lines
    if t.startswith("[") and t.endswith("]"):
        return True
    if "editable:" in t or "generator" in t.lower():
        return True
    return False


def find_forbidden(joined: str, forbidden: list[str], patterns: list[str]) -> list[dict]:
    hits = []
    for w in forbidden:
        if w and w in joined:
            hits.append({"term": w, "kind": "literal"})
    for pat in patterns:
        for m in re.finditer(pat, joined):
            hits.append({"term": m.group(0), "kind": "pattern", "pattern": pat})
    # de-dupe
    seen = set()
    out = []
    for h in hits:
        key = (h["term"], h.get("pattern"))
        if key in seen:
            continue
        seen.add(key)
        out.append(h)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx", type=Path, required=True)
    ap.add_argument("--script", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument(
        "--forbidden",
        nargs="*",
        default=None,
        help="override forbidden literal terms",
    )
    ap.add_argument(
        "--min-coverage",
        type=float,
        default=0.85,
        help="required fraction of required script atoms found in PPTX",
    )
    ap.add_argument(
        "--allow-partial-body",
        action="store_true",
        help="do not fail on long PPTX lines missing from script (still report)",
    )
    args = ap.parse_args()

    pptx = args.pptx.resolve()
    script = load_json(args.script.resolve())
    forbidden = args.forbidden if args.forbidden is not None else list(DEFAULT_FORBIDDEN)

    texts = extract_pptx_texts(pptx)
    joined = "".join(texts)
    joined_norm = normalize(joined)

    # 1) forbidden
    forbidden_hits = find_forbidden(joined, forbidden, DEFAULT_FORBIDDEN_PATTERNS)
    # 维E：script 业务口径允许「维E的100倍」；禁的是「维生素E」整词与好物推荐/锌硒联推
    # 若 script 本身含禁词，记 warning 但不把责任算到生成器（script 侧问题）
    script_blob = json.dumps(script, ensure_ascii=False)
    forbidden_in_script = [h for h in forbidden_hits if h["term"] in script_blob]

    # 2) script coverage
    atoms = script_atoms(script)
    missing = []
    found = []
    for a in atoms:
        needle = a["text"]
        needle_n = normalize(needle)
        ok = needle in joined or needle_n in joined_norm
        if not ok and len(needle) > 8:
            # try progressive shorten
            for L in (12, 10, 8, 6):
                if len(needle) >= L and (needle[:L] in joined or normalize(needle[:L]) in joined_norm):
                    ok = True
                    break
        if ok:
            found.append(a["role"])
        elif a.get("required", True):
            missing.append({"role": a["role"], "text": a["text"]})

    required_total = sum(1 for a in atoms if a.get("required", True))
    required_found = required_total - len(missing)
    coverage = (required_found / required_total) if required_total else 1.0

    # 3) PPTX long lines vs script (anti-invention)
    script_norm_blob = normalize(script_blob)
    invented = []
    for t in texts:
        if is_chrome(t):
            continue
        if len(t) < 8:
            continue
        tn = normalize(t)
        if tn in script_norm_blob or t in script_blob:
            continue
        # allow if any script atom contains this or vice versa
        hit = False
        for a in atoms:
            an = normalize(a["text"])
            if tn in an or an in tn or t in a["text"] or a["text"] in t:
                hit = True
                break
        if not hit:
            # section prefixes like "1、xxx"
            body = re.sub(r"^[一二三四五六七八九十\d]+[、.．]\s*", "", t)
            bn = normalize(body)
            if body and (bn in script_norm_blob or body in script_blob):
                continue
            invented.append(t)

    ok = True
    errors = []
    warnings = []

    # forbidden: fail only if hit and NOT solely from script-allowed medical comparison?
    # Architecture: 禁词 0 命中 in output. 维E in script is OK; 锌/硒/维生素E/好物推荐 must not appear.
    real_forbidden = [h for h in forbidden_hits if h["term"] not in script_blob]
    # If term is in script, still flag if it's in DEFAULT_FORBIDDEN (compliance)
    # For maikenli, script has 维E not 维生素E — good.
    if forbidden_hits:
        # Only fail on hits that are the policy terms
        policy_hits = [
            h
            for h in forbidden_hits
            if h["term"] in forbidden
            or h.get("kind") == "pattern"
        ]
        # Allow if the only hit is substring of a longer allowed medical phrase in script?
        # No — architecture wants 0 hits for 锌/硒/维生素E/好物推荐
        if policy_hits:
            # exception: 硒/锌 as part of unrelated words? patterns already word-ish
            ok = False
            errors.append({"code": "forbidden_term", "hits": policy_hits})

    if coverage < args.min_coverage:
        ok = False
        errors.append(
            {
                "code": "script_coverage_low",
                "coverage": round(coverage, 4),
                "min_coverage": args.min_coverage,
                "missing": missing[:30],
            }
        )
    elif missing:
        warnings.append({"code": "script_atoms_missing", "missing": missing[:20]})

    if invented:
        if args.allow_partial_body:
            warnings.append({"code": "possible_invention", "samples": invented[:20]})
        else:
            # only fail if many invented long lines
            long_inv = [t for t in invented if len(t) >= 12]
            if len(long_inv) >= 3:
                ok = False
                errors.append({"code": "invented_copy", "samples": long_inv[:20]})
            elif long_inv:
                warnings.append({"code": "possible_invention", "samples": long_inv[:10]})

    report = {
        "ok": ok,
        "pptx": str(pptx),
        "script": str(args.script),
        "slide_text_runs": len(texts),
        "forbidden": {
            "terms": forbidden,
            "hits": forbidden_hits,
            "in_script_also": forbidden_in_script,
        },
        "coverage": {
            "ratio": round(coverage, 4),
            "required_total": required_total,
            "required_found": required_found,
            "missing": missing,
            "found_roles_sample": found[:40],
        },
        "invention_check": {
            "suspicious_lines": invented[:40],
            "count": len(invented),
        },
        "errors": errors,
        "warnings": warnings,
        "policy": {
            "copy_source": "script_only",
            "empty_cards": "forbidden",
            "hidden": "excluded",
            "forbidden_terms": "zinc_selenium_vite_好物推荐",
        },
    }

    out = args.out
    if out:
        out = out.resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
