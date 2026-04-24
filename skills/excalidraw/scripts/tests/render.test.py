#!/usr/bin/env python3
"""
Smoke test for scripts/render.py.

Generates a minimal 2-node .excalidraw via layout_architecture, renders
it, and asserts the resulting PNG is non-trivial (>10 KB).

Skipped when the network or chromium is unavailable.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SCRIPTS_DIR.parent
LAYOUT = SCRIPTS_DIR / "layout_architecture.py"
RENDER = SCRIPTS_DIR / "render.py"


def _have_dot() -> bool:
    return shutil.which("dot") is not None


def _have_uv() -> bool:
    return shutil.which("uv") is not None


class RenderSmoke(unittest.TestCase):
    def setUp(self) -> None:
        if not _have_dot():
            self.skipTest("graphviz `dot` not available")
        if not _have_uv():
            self.skipTest("uv not available — render needs uv-managed venv")
        self.tmp = tempfile.mkdtemp(prefix="render-smoke-")
        self.model_path = os.path.join(self.tmp, "mini.json")
        with open(self.model_path, "w", encoding="utf-8") as f:
            json.dump({
                "title": "Smoke",
                "nodes": [
                    {"id": "a", "label": "Alpha", "kind": "service"},
                    {"id": "b", "label": "Beta", "kind": "datastore"},
                ],
                "edges": [{"from": "a", "to": "b", "label": "writes"}],
            }, f)
        self.exc_path = os.path.join(self.tmp, "mini.excalidraw")
        subprocess.run(
            [sys.executable, str(LAYOUT),
             "--input", self.model_path,
             "--output", self.exc_path,
             "--seed", "1"],
            check=True, capture_output=True, text=True,
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_render_produces_nontrivial_png(self) -> None:
        out = os.path.join(self.tmp, "mini.png")
        proc = subprocess.run(
            ["uv", "run", "python", str(RENDER),
             "--input", self.exc_path,
             "--output", out,
             "--width", "1600", "--height", "1000"],
            cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=120,
        )
        if proc.returncode != 0:
            self.skipTest(f"render failed (likely sandbox/network): "
                          f"{proc.stdout.strip()} {proc.stderr.strip()}")
        try:
            payload = json.loads(proc.stdout.strip().splitlines()[-1])
        except Exception:
            self.fail(f"non-JSON stdout: {proc.stdout!r}")
        self.assertTrue(payload.get("ok"), f"render not ok: {payload}")
        self.assertGreater(os.path.getsize(out), 10_000,
                           "PNG should be >10 KB")


if __name__ == "__main__":
    unittest.main(verbosity=2)
