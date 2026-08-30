import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.validate_skills import validate_repository, validate_skill


ROOT = Path(__file__).resolve().parents[1]


class SkillQualityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.skill = self.root / "skills" / "example-skill"
        (self.skill / "evals").mkdir(parents=True)
        (self.skill / "references").mkdir()
        (self.skill / "SKILL.md").write_text(
            """---
name: example-skill
description: Use when a test needs a minimal valid skill.
---

# Example skill

Read [the guide](references/guide.md) when details are needed.
""",
            encoding="utf-8",
        )
        (self.skill / "references" / "guide.md").write_text(
            "# Guide\n", encoding="utf-8"
        )
        self.write_evals()

    def tearDown(self) -> None:
        self.directory.cleanup()

    def write_evals(self, **updates: object) -> None:
        payload: dict[str, object] = {
            "skill_name": "example-skill",
            "evals": [
                {
                    "id": 1,
                    "prompt": "Use the example skill.",
                    "expected_output": "A concise example result.",
                    "assertions": ["The result follows the guide"],
                }
            ],
        }
        payload.update(updates)
        (self.skill / "evals" / "evals.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )

    def test_accepts_a_complete_skill(self) -> None:
        self.assertEqual(validate_skill(self.skill), [])

    def test_enforces_repository_metadata_rules(self) -> None:
        cases = {
            "name does not match directory": """---
name: another-skill
description: Use when a test needs a minimal valid skill.
---
""",
            "name is not kebab case": """---
name: Example_Skill
description: Use when a test needs a minimal valid skill.
---
""",
            "description must start with 'Use when'": """---
name: example-skill
description: A minimal valid skill.
---
""",
            "SKILL.md must be under 500 lines": """---
name: example-skill
description: Use when a test needs a minimal valid skill.
---
"""
            + "instruction\n" * 496,
        }

        for expected, content in cases.items():
            with self.subTest(expected=expected):
                (self.skill / "SKILL.md").write_text(content, encoding="utf-8")
                self.assertTrue(
                    any(expected in error for error in validate_skill(self.skill)),
                    validate_skill(self.skill),
                )

    def test_accepts_folded_yaml_descriptions(self) -> None:
        (self.skill / "SKILL.md").write_text(
            """---
name: example-skill
description: >-
  Use when a test needs a folded YAML description that remains valid.
---

# Example skill

Read [the guide](references/guide.md) when details are needed.
""",
            encoding="utf-8",
        )

        self.assertEqual(validate_skill(self.skill), [])

    def test_requires_a_well_formed_evaluation_contract(self) -> None:
        (self.skill / "evals" / "fixtures").mkdir()
        (self.skill / "evals" / "fixtures" / "input.txt").write_text(
            "fixture", encoding="utf-8"
        )
        valid_eval = {
            "id": "fixture-case",
            "prompt": "Use the fixture.",
            "expected_output": "A fixture-backed result.",
            "assertions": ["The fixture is used"],
            "files": ["evals/fixtures/input.txt"],
        }
        self.write_evals(evals=[valid_eval])
        self.assertEqual(validate_skill(self.skill), [])

        cases = (
            ({"skill_name": "wrong", "evals": [valid_eval]}, "skill_name must match"),
            ({"evals": []}, "skill_name must match"),
            ({"skill_name": "example-skill", "evals": []}, "evals must be a non-empty list"),
            (
                {
                    "skill_name": "example-skill",
                    "evals": [valid_eval, valid_eval],
                },
                "eval IDs must be unique",
            ),
            (
                {
                    "skill_name": "example-skill",
                    "evals": [{**valid_eval, "assertions": []}],
                },
                "assertions must be a non-empty list",
            ),
            (
                {
                    "skill_name": "example-skill",
                    "evals": [{**valid_eval, "files": ["evals/fixtures/missing.txt"]}],
                },
                "fixture does not exist",
            ),
        )

        for payload, expected in cases:
            with self.subTest(expected=expected):
                (self.skill / "evals" / "evals.json").write_text(
                    json.dumps(payload), encoding="utf-8"
                )
                self.assertTrue(
                    any(expected in error for error in validate_skill(self.skill)),
                    validate_skill(self.skill),
                )

        (self.skill / "evals" / "evals.json").unlink()
        self.assertTrue(
            any("evals/evals.json is required" in error for error in validate_skill(self.skill))
        )

    def test_reports_broken_internal_markdown_links(self) -> None:
        (self.skill / "SKILL.md").write_text(
            (self.skill / "SKILL.md").read_text(encoding="utf-8")
            + "\nRead [missing](references/missing.md).\n",
            encoding="utf-8",
        )

        errors = validate_skill(self.skill)

        self.assertTrue(any("broken local link" in error for error in errors), errors)

    def test_requires_resources_to_be_reachable_from_instructions_or_evals(self) -> None:
        scripts = self.skill / "scripts"
        scripts.mkdir()
        helper = scripts / "helper.py"
        helper.write_text("print('ok')\n", encoding="utf-8")

        errors = validate_skill(self.skill)
        self.assertTrue(any("unreachable resource: scripts/helper.py" in error for error in errors))

        guide = self.skill / "references" / "guide.md"
        guide.write_text(
            "# Guide\n\nRun `scripts/helper.py` for deterministic output.\n",
            encoding="utf-8",
        )
        self.assertEqual(validate_skill(self.skill), [])

    def test_does_not_treat_a_longer_path_as_a_resource_reference(self) -> None:
        scripts = self.skill / "scripts"
        scripts.mkdir()
        (scripts / "tool.py").write_text("print('ok')\n", encoding="utf-8")
        (self.skill / "references" / "guide.md").write_text(
            "# Guide\n\nIgnore `scripts/tool.py.bak`.\n", encoding="utf-8"
        )

        errors = validate_skill(self.skill)

        self.assertTrue(any("unreachable resource: scripts/tool.py" in error for error in errors))

    def test_reports_resource_symlinks_that_escape_the_skill(self) -> None:
        scripts = self.skill / "scripts"
        scripts.mkdir()
        outside = self.root / "outside.py"
        outside.write_text("print('outside')\n", encoding="utf-8")
        (scripts / "outside.py").symlink_to(outside)
        (self.skill / "references" / "guide.md").write_text(
            "# Guide\n\nRun `scripts/outside.py`.\n", encoding="utf-8"
        )

        errors = validate_skill(self.skill)

        self.assertTrue(
            any("resource escapes the skill: scripts/outside.py" in error for error in errors),
            errors,
        )

    def test_repository_validation_checks_every_canonical_skill(self) -> None:
        second = self.root / "skills" / "missing-evals"
        second.mkdir()
        (second / "SKILL.md").write_text(
            """---
name: missing-evals
description: Use when proving repository-wide discovery.
---
""",
            encoding="utf-8",
        )

        errors = validate_repository(self.root)

        self.assertTrue(any("missing-evals/evals/evals.json is required" in error for error in errors))

    def test_repository_cli_reports_current_skills_as_valid(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/validate_skills.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Validated", result.stdout)


if __name__ == "__main__":
    unittest.main()
