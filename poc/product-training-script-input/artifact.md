# 商品培训业务 Word 母版复用契约

- Reference: `/Users/liminrong/Projects/chain-pharmacy-content-studio/outputs/courseware-natural-import/商品培训课件_业务填写样本.docx`
- SHA-256: `d7217469d278e187afa9a13fe7d16a6abf30160c20350bd2b5d4716b77245bfd`
- Reference pages: 6
- Sections: 1
- Evidence:
  - `poc/product-training-script-input/reference-business-word-contact-sheet.png`
  - `poc/product-training-script-input/template-style-evidence.json`

## Page system

- US Letter portrait, 8.5 × 11 in.
- Margins: 1 in on all sides.
- Header/footer distance: 0.492 in.
- Single section, no different first page, independent header/footer.

## Typography and components

- Main font: Source Han Sans SC.
- Body: 11 pt, 1.25 line spacing, 6 pt after.
- Existing header, footer and page number are preserve-only.
- `Courseware Ignore` marks business instructions that the script parser must skip.
- Content title uses Heading 1; scene-bearing section titles use Heading 2.
- Instruction callouts use pale fill and restrained accent color.

## Slot map

- Page 1 instructions: replace with the new video/courseware workflow explanation; parser ignores.
- Content title: one Heading 1 paragraph; becomes `project_title`.
- Content sections: any number of Heading 2 paragraphs followed by approved body text; each maps to a scene intent.
- Final asset checklist: parser ignores and remains business guidance.

## Content flow

1. How to fill and what not to fill.
2. Concrete product-training script example.
3. Authorized-asset checklist and preflight review.

## Fidelity gates

- Preserve page geometry, header/footer relationship, page numbering and Chinese font behavior.
- New document may change accent color from company green to the selected product-training blue only in body content.
- No Chinese glyph loss, clipping, overlap, broken headings or empty pages.
- Retained reference must remain unchanged.
