import subprocess
import sys
import unittest
from pathlib import Path

from scripts.ci_scope import Scope, classify_paths


ROOT = Path(__file__).resolve().parents[1]


class CiScopeTest(unittest.TestCase):
    def test_non_skill_markdown_runs_no_heavy_validation(self) -> None:
        paths = (
            "README.md",
            "CHANGELOG.md",
            "docs/architecture.markdown",
            "docs/skills/README.md",
            "plugins/humanize/README.mdx",
        )

        self.assertEqual(classify_paths(paths), Scope(False, False, False))

    def test_skill_markdown_runs_distribution_and_its_scaffold(self) -> None:
        cases = {
            "skills/humanize/SKILL.md": Scope(True, False, False),
            "plugins/humanize/skills/humanize/README.md": Scope(
                True, False, False
            ),
            "skills/python-scaffold/README.md": Scope(True, True, False),
            "plugins/typescript-scaffold/skills/typescript-scaffold/README.mdx": Scope(
                True, False, True
            ),
        }

        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertEqual(classify_paths((path,)), expected)

    def test_release_commit_does_not_run_scaffold_validation(self) -> None:
        paths = (
            ".claude-plugin/plugin.json",
            ".codex-plugin/plugin.json",
            ".release-please-manifest.json",
            "CHANGELOG.md",
            "version.txt",
        )

        self.assertEqual(classify_paths(paths), Scope(True, False, False))

    def test_non_markdown_changes_run_distribution_validation(self) -> None:
        self.assertEqual(
            classify_paths(("scripts/validate_releases.py",)),
            Scope(True, False, False),
        )

    def test_validation_workflow_changes_run_every_suite(self) -> None:
        self.assertEqual(
            classify_paths((".github/workflows/validation.yml",)),
            Scope(True, True, True),
        )

    def test_cli_accepts_null_delimited_git_paths(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/ci_scope.py", "--null"],
            cwd=ROOT,
            input=b"README.md\0skills/python-scaffold/SKILL.md\0",
            check=False,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual(
            result.stdout.decode().splitlines(),
            ["distribution=true", "python=true", "typescript=false"],
        )


if __name__ == "__main__":
    unittest.main()
