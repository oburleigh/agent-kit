import json
import re
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


def workflow_filter_patterns(workflow: str) -> list[str]:
    block = workflow.split("filters: |\n", 1)[1].split("\n\n", 1)[0]
    return [
        line.strip()[3:-1]
        for line in block.splitlines()
        if line.strip().startswith("- '")
    ]


def workflow_push_patterns(workflow: str) -> list[str]:
    block = workflow.split("  push:\n", 1)[1].split("\n\npermissions:", 1)[0]
    return [
        line.strip()[3:-1]
        for line in block.splitlines()
        if line.strip().startswith('- "')
    ]


def matches_filter(path: str, patterns: list[str]) -> bool:
    def pattern_regex(pattern: str) -> str:
        escaped = re.escape(pattern)
        escaped = escaped.replace(r"\*\*/", "(?:.*/)?")
        escaped = escaped.replace(r"\*\*", ".*")
        escaped = escaped.replace(r"\*", "[^/]*")
        return f"^{escaped}$"

    return any(re.fullmatch(pattern_regex(pattern), path) for pattern in patterns)


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

    def test_distribution_workflow_skips_non_skill_markdown(self) -> None:
        workflow = (ROOT / ".github/workflows/plugin-distribution.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("dorny/paths-filter@ceb8a2b8f2d89434be7ff52d3de7ec3738c5cc9d # v4.0.3", workflow)
        self.assertIn("- 'skills/**'", workflow)
        self.assertIn("- 'plugins/*/skills/**'", workflow)
        self.assertNotIn("- 'README.md'", workflow)
        self.assertNotIn("- 'CHANGELOG.md'", workflow)
        required_job = workflow.split("  required:\n", 1)[1]
        self.assertIn("name: Plugin distribution", required_job)
        self.assertIn('test "$CHANGES_RESULT" = "success"', required_job)
        self.assertIn('if [[ "$RELEVANT" == "false" ]]', required_job)
        self.assertIn('test "$RELEVANT" = "true"', required_job)
        self.assertIn('test "$VERIFY_RESULT" = "success"', required_job)

    def test_workflow_filters_scope_markdown_to_skills(self) -> None:
        workflows = {
            name: (
                ROOT / ".github/workflows" / name
            ).read_text(encoding="utf-8")
            for name in (
                "plugin-distribution.yml",
                "python-scaffold.yml",
                "typescript-scaffold.yml",
            )
        }
        distribution_filters = (
            workflow_filter_patterns(workflows["plugin-distribution.yml"]),
            workflow_push_patterns(workflows["plugin-distribution.yml"]),
        )
        python_filters = (
            workflow_filter_patterns(workflows["python-scaffold.yml"]),
            workflow_push_patterns(workflows["python-scaffold.yml"]),
        )
        typescript_filters = (
            workflow_filter_patterns(workflows["typescript-scaffold.yml"]),
            workflow_push_patterns(workflows["typescript-scaffold.yml"]),
        )

        relevant_distribution_paths = (
            "skills/humanize/SKILL.md",
            "plugins/humanize/skills/humanize/README.md",
            "scripts/validate_releases.py",
            "tests/test_plugin_distribution.py",
            ".github/workflows/release-please.yml",
            ".agents/plugins/marketplace.json",
            ".codex-plugin/plugin.json",
            ".release-please-manifest.json",
            "version.txt",
        )
        irrelevant_markdown_paths = (
            "README.md",
            "CHANGELOG.md",
            "docs/README.md",
            "scripts/README.md",
            "tests/README.md",
            ".github/workflows/README.md",
            ".agents/plugins/README.md",
            "plugins/humanize/CHANGELOG.md",
        )
        for distribution in distribution_filters:
            for path in relevant_distribution_paths:
                self.assertTrue(matches_filter(path, distribution), path)
            for path in irrelevant_markdown_paths:
                self.assertFalse(matches_filter(path, distribution), path)

        python_skill = "skills/python-scaffold/README.md"
        packaged_python = (
            "plugins/python-scaffold/skills/python-scaffold/README.md"
        )
        for python in python_filters:
            self.assertTrue(matches_filter(python_skill, python))
            self.assertTrue(matches_filter(packaged_python, python))
            self.assertFalse(matches_filter("skills/humanize/SKILL.md", python))
            self.assertFalse(matches_filter(".release-please-manifest.json", python))

        typescript_skill = "skills/typescript-scaffold/README.md"
        packaged_typescript = (
            "plugins/typescript-scaffold/skills/typescript-scaffold/README.md"
        )
        for typescript in typescript_filters:
            self.assertTrue(matches_filter(typescript_skill, typescript))
            self.assertTrue(matches_filter(packaged_typescript, typescript))
            self.assertFalse(matches_filter("skills/humanize/SKILL.md", typescript))
            self.assertFalse(
                matches_filter(".release-please-manifest.json", typescript)
            )

    def test_pull_requests_report_required_contexts_with_scoped_validation(self) -> None:
        workflows = {
            "plugin-distribution.yml": "Plugin distribution",
            "python-scaffold.yml": "Python scaffold",
            "typescript-scaffold.yml": "TypeScript scaffold",
        }
        for workflow_name, required_check in workflows.items():
            workflow = (ROOT / ".github/workflows" / workflow_name).read_text(
                encoding="utf-8"
            )
            self.assertIn("workflow_dispatch:", workflow)
            pull_request = workflow.split("pull_request:", 1)[1].split("push:", 1)[0]
            self.assertNotIn("paths:", pull_request)
            self.assertEqual(workflow.count(f"name: {required_check}\n"), 2)
            self.assertIn("if: github.event_name == 'push'", workflow)

        for workflow_name in ("python-scaffold.yml", "typescript-scaffold.yml"):
            workflow = (ROOT / ".github/workflows" / workflow_name).read_text(
                encoding="utf-8"
            )
            self.assertNotIn(".release-please-manifest.json", workflow)
            self.assertNotIn("plugins/*/version.txt", workflow)
            self.assertIn(
                "dorny/paths-filter@ceb8a2b8f2d89434be7ff52d3de7ec3738c5cc9d # v4.0.3",
                workflow,
            )
            self.assertIn("outputs:\n      relevant:", workflow)
            self.assertIn("if: needs.changes.outputs.relevant == 'true'", workflow)

        python_workflow = (
            ROOT / ".github/workflows/python-scaffold.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("- 'skills/python-scaffold/**'", python_workflow)
        self.assertIn(
            "- 'plugins/python-scaffold/skills/python-scaffold/**'",
            python_workflow,
        )
        required_job = python_workflow.split("  required:\n", 1)[1]
        self.assertIn("name: Python scaffold", required_job)
        self.assertIn("if: always()", required_job)
        self.assertIn("- changes", required_job)
        self.assertIn("- verify", required_job)
        self.assertIn("- create-only-portability", required_job)
        self.assertIn('test "$CHANGES_RESULT" = "success"', required_job)
        self.assertIn('if [[ "$RELEVANT" == "false" ]]', required_job)
        self.assertIn('test "$RELEVANT" = "true"', required_job)
        self.assertIn('test "$VERIFY_RESULT" = "success"', required_job)
        self.assertIn('test "$PORTABILITY_RESULT" = "success"', required_job)

        typescript_workflow = (
            ROOT / ".github/workflows/typescript-scaffold.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("- 'skills/typescript-scaffold/**'", typescript_workflow)
        self.assertIn(
            "- 'plugins/typescript-scaffold/skills/typescript-scaffold/**'",
            typescript_workflow,
        )
        typescript_required = typescript_workflow.split("  required:\n", 1)[1]
        self.assertIn("name: TypeScript scaffold", typescript_required)
        self.assertIn('test "$CHANGES_RESULT" = "success"', typescript_required)
        self.assertIn('if [[ "$RELEVANT" == "false" ]]', typescript_required)
        self.assertIn('test "$RELEVANT" = "true"', typescript_required)
        self.assertIn('test "$VERIFY_RESULT" = "success"', typescript_required)

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
