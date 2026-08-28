import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.validate_releases import validate_release_configuration


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_releases.py"
BOOTSTRAP_SHA = "a3423d74169d6b1f497399b9cc2a33783800d697"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{json.dumps(value, indent=2)}\n", encoding="utf-8")


def write_component(root: Path, path: str, name: str, version: str) -> None:
    component = root if path == "." else root / path
    write_json(
        component / ".codex-plugin/plugin.json",
        {"name": name, "version": version},
    )
    write_json(
        component / ".claude-plugin/plugin.json",
        {"name": name, "version": version},
    )
    (component / "version.txt").write_text(f"{version}\n", encoding="utf-8")
    (component / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")


def package_config(name: str) -> dict:
    return {
        "release-type": "simple",
        "component": name,
        "version-file": "version.txt",
        "changelog-path": "CHANGELOG.md",
        "extra-files": [
            {
                "type": "json",
                "path": ".codex-plugin/plugin.json",
                "jsonpath": "$.version",
            },
            {
                "type": "json",
                "path": ".claude-plugin/plugin.json",
                "jsonpath": "$.version",
            },
        ],
    }


def create_valid_repository(root: Path) -> None:
    codex_plugins = [
        {"name": "agent-kit", "source": {"source": "local", "path": "./"}},
        {
            "name": "create-skill",
            "source": {"source": "local", "path": "./plugins/create-skill"},
        },
    ]
    claude_plugins = [
        {"name": "agent-kit", "source": "./"},
        {"name": "create-skill", "source": "./plugins/create-skill"},
    ]
    write_json(root / ".agents/plugins/marketplace.json", {"plugins": codex_plugins})
    write_json(root / ".claude-plugin/marketplace.json", {"plugins": claude_plugins})
    write_component(root, ".", "agent-kit", "0.2.0")
    write_component(root, "plugins/create-skill", "create-skill", "0.1.0")
    write_json(
        root / ".release-please-manifest.json",
        {".": "0.2.0", "plugins/create-skill": "0.1.0"},
    )
    write_json(
        root / "release-please-config.json",
        {
            "$schema": "https://raw.githubusercontent.com/googleapis/release-please/v17.6.0/schemas/config.json",
            "bootstrap-sha": BOOTSTRAP_SHA,
            "always-update": True,
            "include-component-in-tag": True,
            "include-v-in-tag": True,
            "tag-separator": "-",
            "separate-pull-requests": False,
            "bump-minor-pre-major": True,
            "bump-patch-for-minor-pre-major": True,
            "packages": {
                ".": package_config("agent-kit"),
                "plugins/create-skill": package_config("create-skill"),
            },
        },
    )


class ReleaseConfigurationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        create_valid_repository(self.root)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def read_json(self, path: str) -> dict:
        return json.loads((self.root / path).read_text(encoding="utf-8"))

    def test_valid_independent_component_configuration_is_accepted(self) -> None:
        self.assertEqual(validate_release_configuration(self.root), [])

    def test_release_manifest_must_cover_every_published_component(self) -> None:
        manifest = self.read_json(".release-please-manifest.json")
        del manifest["plugins/create-skill"]
        write_json(self.root / ".release-please-manifest.json", manifest)

        errors = validate_release_configuration(self.root)

        self.assertIn(
            "release manifest components differ: missing plugins/create-skill",
            errors,
        )

    def test_runtime_manifests_must_match_release_state(self) -> None:
        manifest = self.read_json("plugins/create-skill/.claude-plugin/plugin.json")
        manifest["version"] = "0.1.1"
        write_json(
            self.root / "plugins/create-skill/.claude-plugin/plugin.json", manifest
        )

        errors = validate_release_configuration(self.root)

        self.assertIn(
            "create-skill version drift: release=0.1.0, version.txt=0.1.0, codex=0.1.0, claude=0.1.1",
            errors,
        )

    def test_version_file_must_match_release_state(self) -> None:
        (self.root / "version.txt").write_text("0.3.0\n", encoding="utf-8")

        errors = validate_release_configuration(self.root)

        self.assertIn(
            "agent-kit version drift: release=0.2.0, version.txt=0.3.0, codex=0.2.0, claude=0.2.0",
            errors,
        )

    def test_release_config_must_cover_every_published_component(self) -> None:
        config = self.read_json("release-please-config.json")
        del config["packages"]["plugins/create-skill"]
        write_json(self.root / "release-please-config.json", config)

        errors = validate_release_configuration(self.root)

        self.assertIn(
            "release config components differ: missing plugins/create-skill",
            errors,
        )

    def test_components_must_use_the_independent_pre_one_release_contract(self) -> None:
        config = self.read_json("release-please-config.json")
        config["bump-patch-for-minor-pre-major"] = False
        config["separate-pull-requests"] = True
        config["plugins"] = [
            {
                "type": "linked-versions",
                "groupName": "all",
                "components": ["agent-kit", "create-skill"],
            }
        ]
        config["packages"]["plugins/create-skill"]["release-type"] = "node"
        write_json(self.root / "release-please-config.json", config)

        errors = validate_release_configuration(self.root)

        self.assertIn(
            "release config bump-patch-for-minor-pre-major must be true", errors
        )
        self.assertIn("release config separate-pull-requests must be false", errors)
        self.assertIn("release config must not link component versions", errors)
        self.assertIn("create-skill release-type must be simple", errors)

    def test_release_config_must_pin_its_schema_and_bootstrap_boundary(self) -> None:
        config = self.read_json("release-please-config.json")
        config["$schema"] = (
            "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json"
        )
        config["bootstrap-sha"] = "0" * 40
        config["always-update"] = False
        write_json(self.root / "release-please-config.json", config)

        errors = validate_release_configuration(self.root)

        self.assertIn(
            "release config schema must target release-please v17.6.0", errors
        )
        self.assertIn(
            f"release config bootstrap-sha must be the ADM-188 boundary {BOOTSTRAP_SHA}",
            errors,
        )
        self.assertIn("release config always-update must be true", errors)

    def test_components_must_update_both_runtime_manifests(self) -> None:
        config = self.read_json("release-please-config.json")
        config["packages"]["plugins/create-skill"]["extra-files"].pop()
        write_json(self.root / "release-please-config.json", config)

        errors = validate_release_configuration(self.root)

        self.assertIn(
            "create-skill extra-files must target both runtime manifest versions",
            errors,
        )

    def test_every_component_must_have_a_local_changelog(self) -> None:
        (self.root / "plugins/create-skill/CHANGELOG.md").unlink()

        errors = validate_release_configuration(self.root)

        self.assertIn("create-skill is missing CHANGELOG.md", errors)

    def test_cli_reports_drift_and_exits_nonzero(self) -> None:
        (self.root / "plugins/create-skill/version.txt").write_text(
            "invalid\n", encoding="utf-8"
        )

        result = subprocess.run(
            [sys.executable, VALIDATOR, self.root],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("create-skill version drift", result.stderr)


if __name__ == "__main__":
    unittest.main()
