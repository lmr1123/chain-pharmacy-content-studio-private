# courseware3-pptx-v1

Production entry for the signed-off courseware-3 PPTX layout.

```bash
node export.mjs \
  --model <compiled-content-model.json> \
  --assets <compiled-public-dir> \
  --out <deck.pptx> \
  --qa <qa-dir> \
  --report <generate-report.json>
```

Theme compilation and source-gold removal are handled by
`scripts/replicate_courseware_theme.py`. This engine only renders the compiled,
fully approved model and writes editable PPTX plus per-slide QA evidence.
