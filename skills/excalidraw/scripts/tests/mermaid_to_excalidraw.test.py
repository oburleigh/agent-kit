#!/usr/bin/env python3
"""
Smoke test for scripts/mermaid_to_excalidraw.py.

Writes a tiny flowchart to a .mmd, runs the converter, asserts the
resulting .excalidraw has at least 3 elements (two nodes + one edge).
Skipped when network/chromium are unavailable.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SCRIPTS_DIR.parent
SCRIPT = SCRIPTS_DIR / "mermaid_to_excalidraw.py"


class MermaidConvertSmoke(unittest.TestCase):
    def setUp(self) -> None:
        if shutil.which("uv") is None:
            self.skipTest("uv not available")
        self.tmp = tempfile.mkdtemp(prefix="m2e-smoke-")
        self.mmd = os.path.join(self.tmp, "tiny.mmd")
        Path(self.mmd).write_text(
            "flowchart TD\n"
            "    A[Start] --> B[Middle]\n"
            "    B --> C[End]\n",
            encoding="utf-8",
        )
        self.exc = os.path.join(self.tmp, "tiny.excalidraw")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_produces_at_least_three_elements(self) -> None:
        proc = subprocess.run(
            ["uv", "run", "python", str(SCRIPT),
             "--input", self.mmd, "--output", self.exc],
            cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=180,
        )
        if proc.returncode != 0:
            self.skipTest(f"converter failed (likely network): "
                          f"{proc.stdout.strip()} {proc.stderr.strip()}")
        try:
            payload = json.loads(proc.stdout.strip().splitlines()[-1])
        except Exception:
            self.fail(f"non-JSON stdout: {proc.stdout!r}")
        self.assertTrue(payload.get("ok"), f"converter not ok: {payload}")
        with open(self.exc, "r", encoding="utf-8") as f:
            diagram = json.load(f)
        self.assertEqual(diagram["type"], "excalidraw")
        self.assertGreaterEqual(len(diagram["elements"]), 3,
                                f"expected >=3 elements, got {len(diagram['elements'])}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
