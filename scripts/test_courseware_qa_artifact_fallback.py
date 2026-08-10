#!/usr/bin/env python3
"""Regression tests for fail-closed courseware QA rendering."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_courseware as gc  # noqa: E402


SAMPLE_PPTX = (
    ROOT
    / "production-library/templates/settled/product-courseware-component-v1"
    / "构件化商品培训_默认主路径_签样参考.pptx"
)


def completed(cmd: list[str], code: int, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(cmd, code, stdout=stdout, stderr=stderr)


def fake_artifact_success(qa_dir: Path, count: int = 2):
    def runner(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess:
        if cmd and cmd[0] == "node":
            paths = []
            for index in range(1, count + 1):
                image = qa_dir / f"slide-{index}.png"
                image.write_bytes(b"\x89PNG\r\n\x1a\n" + bytes([index]) * 128)
                paths.append(str(image))
            payload = {
                "ok": True,
                "backend": "artifact-tool",
                "slideCount": count,
                "paths": paths,
            }
            return completed(cmd, 0, json.dumps(payload))
        return completed(cmd, 1, stderr="unexpected command")

    return runner


class CoursewareQaArtifactToolTests(unittest.TestCase):
    def test_qa_uses_only_artifact_tool_without_office_probe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            qa_dir = Path(tmp) / "qa"
            qa_dir.mkdir()
            with mock.patch(
                "shutil.which",
                side_effect=AssertionError("QA must not probe office executables"),
            ) as which, mock.patch.object(
                gc, "run_cmd", side_effect=fake_artifact_success(qa_dir)
            ) as runner:
                paths = gc.render_qa(SAMPLE_PPTX, qa_dir)

            self.assertEqual(len(paths), 2)
            report = json.loads((qa_dir / "qa-render-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["backend"], "artifact-tool")
            self.assertEqual(
                report["attempts"],
                [{"backend": "artifact-tool", "ok": True, "slides": 2}],
            )
            which.assert_not_called()
            [command] = [call.args[0] for call in runner.call_args_list]
            self.assertEqual(command[0], "node")
            self.assertEqual(Path(command[1]), gc.DEFAULT_ARTIFACT_RENDERER)

    def test_qa_source_contains_no_office_renderer_commands(self) -> None:
        source = Path(gc.__file__).read_text(encoding="utf-8")
        render_source = source[source.index("def render_qa(") : source.index("def apply_page_filter(")]
        for token in ("soffice", "libreoffice", "pdftoppm"):
            self.assertNotIn(token, render_source.lower())

    def test_artifact_renderer_failure_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            qa_dir = Path(tmp) / "qa"
            with mock.patch(
                "shutil.which",
                side_effect=AssertionError("QA must not probe office executables"),
            ) as which, mock.patch.object(
                gc,
                "run_cmd",
                return_value=completed(["node"], 1, stderr="artifact import failed"),
            ):
                with self.assertRaises(gc.GeneratorError) as ctx:
                    gc.render_qa(SAMPLE_PPTX, qa_dir)
            message = str(ctx.exception)
            self.assertIn("artifact-tool", message)
            which.assert_not_called()
            report = json.loads((qa_dir / "qa-render-report.json").read_text(encoding="utf-8"))
            self.assertFalse(report["ok"])
            self.assertEqual(len(report["attempts"]), 1)
            self.assertEqual(report["attempts"][0]["backend"], "artifact-tool")

    def test_generator_exit_is_nonzero_when_qa_rendering_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp) / "job"
            draft = job / "draft"
            generated = job / "intake/generated-assets"
            draft.mkdir(parents=True)
            generated.mkdir(parents=True)
            product = job / "intake/product-packshot.png"
            visual = generated / "visual.png"
            product.write_bytes(b"\x89PNG\r\n\x1a\nproduct")
            visual.write_bytes(b"\x89PNG\r\n\x1a\nvisual")
            script_path = draft / "script.structured.json"
            script_path.write_text(
                json.dumps(
                    {
                        "meta": {
                            "display_name": "QA失败样例",
                            "product_packshot": str(product),
                        },
                        "benefits": {
                            "title": "核心知识",
                            "items": [
                                {
                                    "title": "知识点",
                                    "body": "已经审核的说明",
                                    "chain": [
                                        {
                                            "role": "benefit_visual",
                                            "file": str(visual),
                                            "source_kind": "system_generated",
                                        }
                                    ],
                                }
                            ],
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            out = job / "render"

            def fake_export(**kwargs: object) -> dict[str, object]:
                Path(kwargs["out_pptx"]).write_bytes(b"fake-pptx")
                return {"slides": 2, "unknown_types": [], "recipe_trace": [], "font": "Arial"}

            argv = [
                "generate_courseware.py",
                "--script",
                str(script_path),
                "--out-dir",
                str(out),
                "--skip-provenance",
            ]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                gc, "build_manifest"
            ), mock.patch.object(gc, "export_pptx", side_effect=fake_export), mock.patch.object(
                gc, "render_qa", side_effect=gc.GeneratorError("artifact-tool renderer failed")
            ):
                code = gc.main()

            self.assertEqual(code, 1)
            report = json.loads((out / "generate-report.json").read_text(encoding="utf-8"))
            self.assertFalse(report["ok"])
            self.assertIn("artifact-tool renderer failed", report["qa_error"])

    def test_project_renderer_renders_every_slide_to_png(self) -> None:
        renderer = (
            ROOT
            / "production-library/engines/courseware-pptx-v1/render-pptx.mjs"
        )
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "slides"
            proc = subprocess.run(
                [
                    "node",
                    str(renderer),
                    "--input",
                    str(SAMPLE_PPTX),
                    "--output-dir",
                    str(output),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
            report = json.loads(proc.stdout)
            pngs = sorted(output.glob("slide-*.png"))
            self.assertEqual(len(pngs), report["slideCount"])
            self.assertTrue(all(path.stat().st_size > 100 for path in pngs))

        with zipfile.ZipFile(SAMPLE_PPTX) as archive:
            presentation_xml = archive.read("ppt/presentation.xml")
        self.assertEqual(report["slideCount"], presentation_xml.count(b"<p:sldId "))


if __name__ == "__main__":
    unittest.main()
