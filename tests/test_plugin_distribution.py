import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODEX_MARKETPLACE = ROOT / ".agents/plugins/marketplace.json"
CLAUDE_MARKETPLACE = ROOT / ".claude-plugin/marketplace.json"
AGGREGATE_PLUGIN = ROOT
SKILLS = ROOT / "skills"


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def skill_files(root: Path) -> dict[str, bytes]:
    ignored = {
        ".coverage",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "htmlcov",
        "node_modules",
    }
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
        and not ignored.intersection(path.relative_to(root).parts)
        and path.suffix != ".whl"
        and not path.name.endswith(".tar.gz")
    }


class PluginDistributionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.codex = read_json(CODEX_MARKETPLACE)
        self.claude = read_json(CLAUDE_MARKETPLACE)

    def test_marketplaces_publish_the_same_plugins(self) -> None:
        codex_names = [plugin["name"] for plugin in self.codex["plugins"]]
        claude_names = [plugin["name"] for plugin in self.claude["plugins"]]
        plugin_names = ["agent-kit", *sorted(
            path.name
            for path in (ROOT / "plugins").iterdir()
            if (path / ".codex-plugin/plugin.json").exists()
        )]

        self.assertEqual(codex_names, sorted(codex_names))
        self.assertEqual(codex_names, claude_names)
        self.assertEqual(codex_names, plugin_names)

    def test_every_plugin_is_opt_in_and_runtime_versions_match(self) -> None:
        for plugin in self.codex["plugins"]:
            name = plugin["name"]
            plugin_root = ROOT if name == "agent-kit" else ROOT / "plugins" / name
            codex_manifest = read_json(plugin_root / ".codex-plugin/plugin.json")
            claude_manifest = read_json(plugin_root / ".claude-plugin/plugin.json")

            expected_path = "./" if name == "agent-kit" else f"./plugins/{name}"
            self.assertEqual(plugin["source"], {"source": "local", "path": expected_path})
            self.assertEqual(plugin["policy"]["installation"], "AVAILABLE")
            self.assertEqual(codex_manifest["name"], name)
            self.assertEqual(claude_manifest["name"], name)
            self.assertEqual(codex_manifest["version"], claude_manifest["version"])

    def test_claude_sources_are_local_plugin_directories(self) -> None:
        for plugin in self.claude["plugins"]:
            expected_source = "./" if plugin["name"] == "agent-kit" else f"./plugins/{plugin['name']}"
            self.assertEqual(plugin["source"], expected_source)

    def test_agent_kit_plugin_bundles_every_individual_skill(self) -> None:
        individual_plugin_names = sorted(
            plugin["name"]
            for plugin in self.codex["plugins"]
            if plugin["name"] != "agent-kit"
        )
        codex_manifest = read_json(AGGREGATE_PLUGIN / ".codex-plugin/plugin.json")
        claude_manifest = read_json(AGGREGATE_PLUGIN / ".claude-plugin/plugin.json")

        self.assertEqual(codex_manifest["skills"], "./skills/")
        self.assertEqual(claude_manifest["skills"], "./skills/")
        self.assertTrue(SKILLS.is_dir())
        self.assertEqual(
            sorted(path.name for path in SKILLS.iterdir() if (path / "SKILL.md").is_file()),
            individual_plugin_names,
        )

    def test_standalone_plugins_are_generated_from_canonical_skills(self) -> None:
        for plugin in self.codex["plugins"]:
            name = plugin["name"]
            if name == "agent-kit":
                continue

            canonical = SKILLS / name
            packaged = ROOT / "plugins" / name / "skills" / name
            self.assertEqual(
                skill_files(packaged),
                skill_files(canonical),
                f"{name} standalone package differs from its canonical skill",
            )

    def test_readme_leads_with_one_command_full_install(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("codex plugin add agent-kit@agent-kit", readme)
        self.assertIn("claude plugin install agent-kit@agent-kit", readme)
        self.assertNotIn("## TypeScript scaffold", readme)

    def test_pull_requests_report_all_required_contexts_from_one_workflow(self) -> None:
        workflow_root = ROOT / ".github/workflows"
        workflow = (workflow_root / "validation.yml").read_text(encoding="utf-8")

        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("pull_request:", workflow)
        self.assertNotIn("\n  push:", workflow)
        self.assertIn(
            'python3 scripts/ci_scope.py --base "$BASE_SHA" --head "$HEAD_SHA"',
            workflow,
        )
        self.assertIn("name: ${{ matrix.check }}", workflow)
        self.assertEqual(workflow.count("  required:\n"), 1)
        for required_check in (
            "Plugin distribution",
            "Python scaffold",
            "TypeScript scaffold",
        ):
            self.assertEqual(workflow.count(f"check: {required_check}\n"), 1)

        for obsolete in (
            "plugin-distribution.yml",
            "python-scaffold.yml",
            "typescript-scaffold.yml",
        ):
            self.assertFalse((workflow_root / obsolete).exists())

    def test_required_check_matrix_fails_closed(self) -> None:
        workflow = (ROOT / ".github/workflows/validation.yml").read_text(
            encoding="utf-8"
        )
        required_job = workflow.split("  required:\n", 1)[1]
        gate = required_job.split("        run: |\n", 1)[1]
        cases = (
            (
                {
                    "SCOPE_RESULT": "success",
                    "RELEVANT": "false",
                    "RESULTS": "skipped",
                },
                0,
            ),
            (
                {
                    "SCOPE_RESULT": "success",
                    "RELEVANT": "true",
                    "RESULTS": "success success",
                },
                0,
            ),
            (
                {
                    "SCOPE_RESULT": "success",
                    "RELEVANT": "true",
                    "RESULTS": "success failure",
                },
                1,
            ),
            (
                {
                    "SCOPE_RESULT": "failure",
                    "RELEVANT": "false",
                    "RESULTS": "skipped",
                },
                1,
            ),
            (
                {
                    "SCOPE_RESULT": "success",
                    "RELEVANT": "",
                    "RESULTS": "skipped",
                },
                1,
            ),
            (
                {
                    "SCOPE_RESULT": "success",
                    "RELEVANT": "true",
                    "RESULTS": "",
                },
                1,
            ),
        )

        for environment, expected in cases:
            with self.subTest(environment=environment):
                result = subprocess.run(
                    ["/bin/bash", "-e", "-o", "pipefail", "-c", gate],
                    env=environment,
                    check=False,
                )
                self.assertEqual(result.returncode, expected)

    def test_release_workflow_reconciles_native_checks_with_scoped_permissions(self) -> None:
        workflow = (ROOT / ".github/workflows/release-please.yml").read_text(
            encoding="utf-8"
        )

        release_job, approval_job = workflow.split("  approve-release-checks:\n", 1)

        self.assertIn("workflow_dispatch:", workflow)
        self.assertEqual(workflow.count("if: github.ref == 'refs/heads/main'"), 2)
        self.assertIn("concurrency:", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertNotIn("actions: write", release_job)
        self.assertIn("actions: write", approval_job)
        self.assertIn("needs: release", approval_job)
        self.assertIn("contents: read", approval_job)
        self.assertIn("pull-requests: read", approval_job)
        self.assertIn("persist-credentials: false", approval_job)
        self.assertIn("needs.release.outputs.release_prs", approval_job)
        self.assertIn("python3 scripts/approve_release_checks.py", approval_job)
        self.assertNotIn("steps.release.outputs.prs_created", workflow)
        self.assertNotIn("gh workflow run", workflow)

    def test_release_configuration_passes_repository_validation(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/validate_releases.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_github_actions_use_immutable_versioned_pins(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/check_github_actions.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_internal_planning_artifacts_are_not_published(self) -> None:
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        tracked = subprocess.run(
            ["git", "ls-files", "docs/superpowers"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        self.assertIn("docs/superpowers/", gitignore.splitlines())
        self.assertEqual(tracked, "")

    def test_published_skills_have_codex_interface_metadata(self) -> None:
        skill_names = {
            plugin["name"]
            for plugin in self.codex["plugins"]
            if plugin["name"] != "agent-kit"
        }

        for name in skill_names:
            skill_root = SKILLS / name
            openai_yaml = skill_root / "agents/openai.yaml"
            description = (skill_root / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1]

            self.assertTrue(openai_yaml.is_file(), f"{name} has no agents/openai.yaml")
            openai_metadata = openai_yaml.read_text(encoding="utf-8")
            self.assertIn("interface:", openai_metadata)
            self.assertIn(f"${name}", openai_metadata)
            self.assertNotIn("allow_implicit_invocation: false", openai_metadata)
            self.assertRegex(description, r'description:\s+["\']?Use when')
            self.assertNotIn("disable-model-invocation", description)

    def test_published_skill_guidance_is_runtime_neutral(self) -> None:
        forbidden_shared_phrases = (
            "Claude Code",
            "Codex",
            "~/.claude/",
            "<repo>/.claude/",
            "~/.codex/",
            "<repo>/.codex/",
            "CLAUDE_SKILL_DIR",
            "CODEX_HOME",
            "What Claude wrote",
        )

        for plugin in self.codex["plugins"]:
            if plugin["name"] == "agent-kit":
                continue

            name = plugin["name"]
            skill_root = SKILLS / name
            shared_guidance = [skill_root / "SKILL.md", *(skill_root / "references").glob("*.md")]

            for path in shared_guidance:
                content = path.read_text(encoding="utf-8")
                for phrase in forbidden_shared_phrases:
                    self.assertNotIn(phrase, content, f"{path} assumes one runtime")

            readme = (skill_root / "README.md").read_text(encoding="utf-8")
            self.assertEqual(
                "Claude Code" in readme,
                "Codex" in readme,
                f"{skill_root / 'README.md'} documents only one runtime",
            )

    def test_plugins_do_not_package_legacy_commands(self) -> None:
        for plugin_root in (ROOT / "plugins").iterdir():
            if plugin_root.is_dir():
                self.assertFalse((plugin_root / "commands").exists())

    def test_plugin_directories_are_published_or_explicitly_unpublished(self) -> None:
        published = {plugin["name"] for plugin in self.codex["plugins"]}

        for plugin_root in (ROOT / "plugins").iterdir():
            if not plugin_root.is_dir():
                continue
            has_codex_manifest = (plugin_root / ".codex-plugin/plugin.json").exists()
            has_claude_manifest = (plugin_root / ".claude-plugin/plugin.json").exists()
            is_unpublished = (plugin_root / ".unpublished-plugin").exists()

            self.assertEqual(has_codex_manifest, has_claude_manifest)
            self.assertNotEqual(has_codex_manifest, is_unpublished)
            self.assertEqual(plugin_root.name in published, has_codex_manifest)


if __name__ == "__main__":
    unittest.main()
