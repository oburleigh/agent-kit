import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HUMANIZE = ROOT / "skills" / "humanize"


class HumanizeContractTest(unittest.TestCase):
    def test_learning_state_uses_one_external_config_root(self) -> None:
        skill = (HUMANIZE / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("AGENT_KIT_CONFIG_HOME", skill)
        self.assertIn("humanize/corrections.md", skill)
        self.assertIn("humanize/rules.md", skill)
        self.assertIn("Never write to files inside the installed skill", skill)
        self.assertNotIn(
            "log the correction to `references/corrections.md`", skill
        )

    def test_config_root_has_safe_unix_and_windows_defaults(self) -> None:
        skill = (HUMANIZE / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("$XDG_CONFIG_HOME/agent-kit", skill)
        self.assertIn("$HOME/.config/agent-kit", skill)
        self.assertIn(r"%APPDATA%\agent-kit", skill)
        self.assertIn("non-empty absolute path", skill)
        self.assertIn("Ignore a relative `XDG_CONFIG_HOME`", skill)
        self.assertIn("outside the installed skill and plugin caches", skill)

    def test_learned_state_cannot_escape_the_config_root(self) -> None:
        skill = (HUMANIZE / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("each state path", skill)
        self.assertIn("outside the resolved config root", skill)
        self.assertIn("immediately before every read or write", skill)

        evaluations = json.loads(
            (HUMANIZE / "evals/evals.json").read_text(encoding="utf-8")
        )["evals"]
        containment = next(
            evaluation for evaluation in evaluations if evaluation["id"] == 6
        )
        combined = " ".join(
            [containment["prompt"], containment["expected_output"]]
            + containment["assertions"]
        )
        self.assertIn("symbolic link", combined)
        self.assertIn("outside the config root", combined)

    def test_corrections_require_explicit_persistence_consent(self) -> None:
        skill = (HUMANIZE / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("A correction alone is not permission to persist it", skill)
        self.assertIn("asks you to remember", skill)
        self.assertIn("confirms persistence", skill)
        self.assertIn("Do not prune automatically", skill)
        self.assertIn("archive", skill)

    def test_readme_documents_resolved_config_paths(self) -> None:
        readme = (HUMANIZE / "README.md").read_text(encoding="utf-8")

        self.assertIn("`AGENT_KIT_CONFIG_HOME`", readme)
        self.assertIn("`%APPDATA%\\agent-kit`", readme)
        self.assertIn("`$XDG_CONFIG_HOME/agent-kit`", readme)
        self.assertIn("`$HOME/.config/agent-kit`", readme)
        self.assertIn("humanize/rules.md", readme)
        self.assertIn("humanize/corrections.md", readme)

    def test_evaluations_cover_read_only_plugin_updates(self) -> None:
        evaluations = json.loads(
            (HUMANIZE / "evals/evals.json").read_text(encoding="utf-8")
        )["evals"]
        persistent = next(
            evaluation
            for evaluation in evaluations
            if evaluation["id"] == 4
        )

        combined = " ".join(
            [persistent["prompt"], persistent["expected_output"]]
            + persistent["assertions"]
        )
        self.assertIn("read-only", combined)
        self.assertIn("plugin update", combined)
        self.assertIn("AGENT_KIT_CONFIG_HOME", combined)
        self.assertIn("Codex and Claude", combined)
        self.assertIn("temporary config root", combined)
        self.assertIn("first fresh invocation", combined)
        self.assertIn("replacement plugin", combined)
        self.assertIn("second fresh invocation", combined)

        consent = next(
            evaluation for evaluation in evaluations if evaluation["id"] == 5
        )
        consent_contract = " ".join(
            [consent["prompt"], consent["expected_output"]] + consent["assertions"]
        )
        self.assertIn("correction alone", consent_contract)
        self.assertIn("does not write", consent_contract.lower())


if __name__ == "__main__":
    unittest.main()
