#!/usr/bin/env python3
"""Tests for scripts/validate_skill.py."""

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
SCRIPT = SCRIPTS_DIR / "validate_skill.py"

sys.path.insert(0, str(SCRIPTS_DIR))
import validate_skill as vs  # noqa: E402


def _make_skill(root: Path, *, body: str = "", refs: list[str] | None = None,
                with_theme: bool = False, theme_text: str | None = None) -> None:
    root.mkdir(parents=True, exist_ok=True)
    fm = (
        "---\n"
        "name: testskill\n"
        "description: A test skill description.\n"
        "---\n"
    )
    (root / "SKILL.md").write_text(fm + body, encoding="utf-8")
    if refs:
        (root / "references").mkdir(exist_ok=True)
        for r in refs:
            (root / "references" / r).write_text("placeholder\n", encoding="utf-8")
    if with_theme:
        (root / "theme.json").write_text(
            theme_text if theme_text is not None
            else json.dumps({"colors": {}}),
            encoding="utf-8",
        )


class HappyPath(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="vs-happy-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_ok_when_all_refs_mentioned(self) -> None:
        body = "Sample body with mentions of foo.md and bar.md.\n"
        _make_skill(self.tmp, body=body, refs=["foo.md", "bar.md"],
                    with_theme=True)
        r = vs.validate_skill(self.tmp)
        self.assertTrue(r["ok"], r.get("errors"))
        self.assertEqual(r["name"], "testskill")
        self.assertEqual(set(r["references"]),
                         {"references/foo.md", "references/bar.md"})


class Failures(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="vs-fail-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_missing_skill_md(self) -> None:
        r = vs.validate_skill(self.tmp)
        self.assertFalse(r["ok"])
        self.assertIn("SKILL.md not found", r["errors"][0])

    def test_unmentioned_reference_fails(self) -> None:
        _make_skill(self.tmp, body="No mentions.\n", refs=["lonely.md"])
        r = vs.validate_skill(self.tmp)
        self.assertFalse(r["ok"])
        self.assertTrue(any("lonely.md" in e for e in r["errors"]))

    def test_invalid_theme_json(self) -> None:
        _make_skill(self.tmp, body="Body.\n", with_theme=True,
                    theme_text="{not json")
        r = vs.validate_skill(self.tmp)
        self.assertFalse(r["ok"])
        self.assertTrue(any("theme.json invalid" in e for e in r["errors"]))

    def test_oversized_skill_md(self) -> None:
        body = "\n".join(["padding"] * 500) + "\n"
        _make_skill(self.tmp, body=body)
        r = vs.validate_skill(self.tmp)
        self.assertFalse(r["ok"])
        self.assertTrue(any("must be under 400" in e for e in r["errors"]))

    def test_frontmatter_missing_name(self) -> None:
        (self.tmp / "SKILL.md").write_text(
            "---\ndescription: only desc\n---\nbody\n",
            encoding="utf-8",
        )
        r = vs.validate_skill(self.tmp)
        self.assertFalse(r["ok"])
        self.assertTrue(any("missing `name`" in e for e in r["errors"]))


class CliExits(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="vs-cli-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_help(self) -> None:
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0)
        self.assertIn("--skill", r.stdout)

    def test_failure_exits_one(self) -> None:
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--skill", str(self.tmp)],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 1)
        payload = json.loads(r.stderr)
        self.assertFalse(payload["ok"])

    def test_success_exits_zero(self) -> None:
        _make_skill(self.tmp, body="Body that mentions ref.md.\n",
                    refs=["ref.md"])
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--skill", str(self.tmp)],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        payload = json.loads(r.stdout)
        self.assertTrue(payload["ok"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
