#!/usr/bin/env python3
"""Regression tests for PPT image-slot fit contracts."""

from __future__ import annotations

import base64
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTEXT = ROOT / "production-library/engines/courseware-pptx-v1/lib/context.mjs"
IMAGE_CHAIN = ROOT / "production-library/engines/courseware-pptx-v1/components/image_chain.mjs"


class CoursewareImageSlotTests(unittest.TestCase):
    def test_cover_fills_slot_while_contain_preserves_aspect(self) -> None:
        # 2x1 PNG; enough for context.mjs to read the IHDR width/height.
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAIAAAABCAQAAAB2iJ3eAAAADElEQVR42mNk+M8AAAICAQB7CYQ0AAAAAElFTkSuQmCC"
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            image = tmp_path / "wide.png"
            image.write_bytes(png)
            runner = tmp_path / "check.mjs"
            script = """
import {createContext} from __CONTEXT__;
const calls = [];
const slide = {images: {add: (opts) => { calls.push(opts); return opts; }}};
const style = {canvas: {design_width_px: 1920, design_height_px: 1080, pptx_width_px: 1280, pptx_height_px: 720}, type: {}, font: 'Arial', colors: {}};
const ctx = createContext({model: {}, style, assetsRoot: '/', repoRoot: '/'});
await ctx.imageFit(slide, 'contain', __IMAGE__, 0, 0, 400, 400, 'contain');
await ctx.imageFit(slide, 'cover', {src: __IMAGE__, fit: 'cover'}, 0, 0, 400, 400, 'cover');
console.log(JSON.stringify(calls.map((it) => ({fit: it.fit, position: it.position}))));
"""
            runner.write_text(
                script.replace("__CONTEXT__", json.dumps(CONTEXT.as_uri())).replace(
                    "__IMAGE__", json.dumps(str(image))
                ),
                encoding="utf-8",
            )
            proc = subprocess.run(
                ["node", str(runner)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

        contain, cover = json.loads(proc.stdout)
        self.assertEqual(contain["fit"], "fill")
        self.assertAlmostEqual(contain["position"]["width"], 400 * 1280 / 1920)
        self.assertAlmostEqual(contain["position"]["height"], 200 * 720 / 1080)
        self.assertEqual(cover["fit"], "cover")
        self.assertAlmostEqual(cover["position"]["width"], 400 * 1280 / 1920)
        self.assertAlmostEqual(cover["position"]["height"], 400 * 720 / 1080)

    def test_explicit_wide_benefit_chain_preserves_frame_and_fit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner = Path(tmp) / "check-chain.mjs"
            script = """
import {imageChain} from __IMAGE_CHAIN__;
const calls = [];
const ctx = {
  eid: (...parts) => parts.join('.'),
  imageFit: async (_slide, id, source, cx, cy, w, h, alt) => calls.push({id, source, cx, cy, w, h, alt}),
};
await imageChain(ctx, {}, 'P03', [{
  role: 'benefit_visual_1', file: '/tmp/benefit.png', w: 1200, h: 580,
  fit: 'cover', crop: {x: 0.05, y: 0, w: 0.9, h: 1}
}], {y: 80, totalSpan: 1600});
console.log(JSON.stringify(calls));
"""
            runner.write_text(
                script.replace("__IMAGE_CHAIN__", json.dumps(IMAGE_CHAIN.as_uri())),
                encoding="utf-8",
            )
            proc = subprocess.run(
                ["node", str(runner)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

        [call] = json.loads(proc.stdout)
        self.assertEqual(call["w"], 1200)
        self.assertEqual(call["h"], 580)
        self.assertEqual(call["cy"], 80)
        self.assertEqual(call["source"]["fit"], "cover")
        self.assertEqual(call["source"]["crop"]["w"], 0.9)


if __name__ == "__main__":
    unittest.main()
