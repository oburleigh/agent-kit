#!/usr/bin/env python3
"""Tests for scripts/run_evals.py."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SCRIPTS_DIR / "run_evals.py"
SKILL_ROOT = SCRIPTS_DIR.parent

sys.path.insert(0, str(SCRIPTS_DIR))
import run_evals as re_  # noqa: E402


class GradingHelpers(unittest.TestCase):
    def test_build_grading_prompt_lists_every_dim(self) -> None:
        out = re_.build_grading_prompt({"a": "first", "b": "second"})
        self.assertIn("- a: first", out)
        self.assertIn("- b: second", out)
        self.assertIn("strict JSON", out)

    def test_score_sums_dims(self) -> None:
        result = re_.score_from_grading({
            "a": {"score": 2, "evidence": "x"},
            "b": {"score": 1, "evidence": "y"},
            "c": {"score": 0, "evidence": "z"},
        })
        self.assertEqual(result["total"], 3)
        self.assertEqual(result["max"], 6)


class Scaffolding(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="re-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_creates_workspace_per_case(self) -> None:
        ws = self.tmp / "ws"
        result = re_.scaffold(ws, SKILL_ROOT / "evals" / "evals.json")
        self.assertGreaterEqual(result["cases"], 1)
        # Inspect first case directory.
        with open(SKILL_ROOT / "evals" / "evals.json", "r", encoding="utf-8") as f:
            spec = json.load(f)
        first_id = spec["evals"][0]["id"]
        for lane in ("with_skill", "without_skill"):
            self.assertTrue((ws / f"eval-{first_id}" / lane / "TODO.md").exists())
            self.assertTrue((ws / f"eval-{first_id}" / lane / "outputs").is_dir())
            self.assertTrue((ws / f"eval-{first_id}" / lane / "timing.json").exists())
        self.assertTrue((ws / "benchmark.json").exists())


class CliExits(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="re-cli-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_help(self) -> None:
        r = subprocess.run([sys.executable, str(SCRIPT), "--help"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertIn("--workspace", r.stdout)

    def test_runs_to_zero_exit(self) -> None:
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--workspace", str(self.tmp / "out")],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        payload = json.loads(r.stdout)
        self.assertTrue(payload["ok"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
