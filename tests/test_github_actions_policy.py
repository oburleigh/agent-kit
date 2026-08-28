import tempfile
import unittest
from pathlib import Path

from scripts.check_github_actions import find_unpinned_actions, validate_workflows


SHA = "0123456789abcdef0123456789abcdef01234567"


class GithubActionsPolicyTest(unittest.TestCase):
    def test_accepts_sha_pins_with_version_comments_in_yaml_scalar_forms(self) -> None:
        workflow = f"""
steps:
  - uses: actions/checkout@{SHA} # v7
  - uses: 'astral-sh/setup-uv@{SHA}' # v9.0.0
  - uses: "googleapis/release-please-action@{SHA}" # v5.0.0
"""

        self.assertEqual(find_unpinned_actions(workflow, "release.yml"), [])

    def test_accepts_local_and_docker_actions_without_sha_pins(self) -> None:
        workflow = """
steps:
  - uses: ./.github/actions/verify
  - uses: docker://alpine:3.22
"""

        self.assertEqual(find_unpinned_actions(workflow, "verify.yml"), [])

    def test_accepts_pinned_reusable_workflows(self) -> None:
        workflow = f"""
jobs:
  verify:
    uses: owner/repository/.github/workflows/verify.yml@{SHA} # v2.4.0
"""

        self.assertEqual(find_unpinned_actions(workflow, "verify.yml"), [])

    def test_rejects_unsupported_uses_key_forms_instead_of_skipping_them(self) -> None:
        cases = (
            f'  - "uses": actions/checkout@{SHA} # v7',
            f"  - 'uses': actions/checkout@{SHA} # v7",
            f'  - "u\\x73es": actions/checkout@{SHA} # v7',
            f"  - {{ uses: actions/checkout@{SHA} }} # v7",
            f'  - {{ "u\\x73es": actions/checkout@{SHA} }} # v7',
            f"  - !!str uses: actions/checkout@{SHA} # v7",
            f"  - &action-key uses: actions/checkout@{SHA} # v7",
            f"  - *action-key: actions/checkout@{SHA} # v7",
            f"  - ? uses\n    : actions/checkout@{SHA} # v7",
            "verify: { uses: owner/repository/.github/workflows/verify.yml@v2 }",
            "jobs: { verify: { uses: owner/repository/.github/workflows/verify.yml@v2 } }",
            "verify: !!map { uses: owner/repository/.github/workflows/verify.yml@v2 }",
        )

        for line in cases:
            with self.subTest(line=line):
                errors = find_unpinned_actions(f"steps:\n{line}\n", "workflow.yml")
                self.assertEqual(len(errors), 1)
                self.assertIn("unsupported uses syntax", errors[0])

    def test_allows_github_expressions_containing_double_braces(self) -> None:
        workflow = "if: ${{ github.ref == 'refs/heads/main' }}\n"

        self.assertEqual(find_unpinned_actions(workflow, "workflow.yml"), [])

    def test_rejects_mutable_or_malformed_third_party_references(self) -> None:
        cases = {
            "branch": "actions/checkout@main # v7",
            "tag": "actions/checkout@v7 # v7",
            "short SHA": "actions/checkout@0123456789abcdef # v7",
            "uppercase SHA": f"actions/checkout@{SHA.upper()} # v7",
            "missing comment": f"actions/checkout@{SHA}",
            "non-version comment": f"actions/checkout@{SHA} # pinned",
            "comment hidden in quotes": f'"actions/checkout@{SHA} # v7"',
        }

        for label, value in cases.items():
            with self.subTest(label=label):
                errors = find_unpinned_actions(
                    f"steps:\n  - uses: {value}\n", "workflow.yml"
                )
                self.assertEqual(len(errors), 1)
                self.assertIn(
                    "third-party action must use a 40-character lowercase SHA",
                    errors[0],
                )

    def test_ignores_uses_text_that_is_not_a_yaml_key(self) -> None:
        workflow = """
steps:
  - run: echo 'uses: actions/checkout@v7'
"""

        self.assertEqual(find_unpinned_actions(workflow, "verify.yml"), [])

    def test_directory_validation_scans_yml_and_yaml_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workflows = root / ".github/workflows"
            workflows.mkdir(parents=True)
            (workflows / "valid.yml").write_text(
                f"steps:\n  - uses: actions/checkout@{SHA} # v7\n",
                encoding="utf-8",
            )
            (workflows / "invalid.yaml").write_text(
                "steps:\n  - uses: actions/checkout@v7\n",
                encoding="utf-8",
            )

            errors = validate_workflows(root)

            self.assertEqual(len(errors), 1)
            self.assertIn(".github/workflows/invalid.yaml:2", errors[0])


if __name__ == "__main__":
    unittest.main()
