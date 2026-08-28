import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.ci_scope import Scope, classify_git_diff, classify_paths

ROOT = Path(__file__).resolve().parents[1]


class CiScopeTest(unittest.TestCase):
    def init_repository(self, root: Path) -> None:
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "ci-scope@example.test"],
            cwd=root,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "CI Scope Test"],
            cwd=root,
            check=True,
        )

    def commit(self, root: Path, message: str) -> str:
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, check=True)
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

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

    def test_git_diff_ignores_changes_made_only_on_the_advanced_base(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.init_repository(root)
            (root / "README.md").write_text("base\n", encoding="utf-8")
            scaffold = root / "skills/python-scaffold/example.py"
            scaffold.parent.mkdir(parents=True)
            scaffold.write_text("base = True\n", encoding="utf-8")
            self.commit(root, "initial")

            subprocess.run(["git", "switch", "-q", "-c", "topic"], cwd=root, check=True)
            (root / "README.md").write_text("topic\n", encoding="utf-8")
            head = self.commit(root, "edit readme")

            subprocess.run(["git", "switch", "-q", "main"], cwd=root, check=True)
            scaffold.write_text("base = False\n", encoding="utf-8")
            base = self.commit(root, "advance base")

            self.assertEqual(
                classify_git_diff(base, head, cwd=root),
                Scope(False, False, False),
            )

    def test_git_diff_scopes_a_file_moved_out_of_a_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.init_repository(root)
            scaffold = root / "skills/python-scaffold/example.py"
            scaffold.parent.mkdir(parents=True)
            scaffold.write_text("scaffold = True\n", encoding="utf-8")
            base = self.commit(root, "initial")

            subprocess.run(["git", "switch", "-q", "-c", "topic"], cwd=root, check=True)
            destination = root / "docs/example.py"
            destination.parent.mkdir()
            subprocess.run(
                ["git", "mv", scaffold.relative_to(root), destination.relative_to(root)],
                cwd=root,
                check=True,
            )
            head = self.commit(root, "move scaffold file")

            self.assertEqual(
                classify_git_diff(base, head, cwd=root),
                Scope(True, True, False),
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
