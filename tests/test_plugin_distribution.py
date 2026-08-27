import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODEX_MARKETPLACE = ROOT / ".agents/plugins/marketplace.json"
CLAUDE_MARKETPLACE = ROOT / ".claude-plugin/marketplace.json"


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


class PluginDistributionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.codex = read_json(CODEX_MARKETPLACE)
        self.claude = read_json(CLAUDE_MARKETPLACE)

    def test_marketplaces_publish_the_same_plugins(self) -> None:
        codex_names = [plugin["name"] for plugin in self.codex["plugins"]]
        claude_names = [plugin["name"] for plugin in self.claude["plugins"]]
        plugin_names = sorted(
            path.name
            for path in (ROOT / "plugins").iterdir()
            if (path / ".codex-plugin/plugin.json").exists()
        )

        self.assertEqual(codex_names, sorted(codex_names))
        self.assertEqual(codex_names, claude_names)
        self.assertEqual(codex_names, plugin_names)

    def test_every_plugin_is_opt_in_and_runtime_versions_match(self) -> None:
        for plugin in self.codex["plugins"]:
            name = plugin["name"]
            plugin_root = ROOT / "plugins" / name
            codex_manifest = read_json(plugin_root / ".codex-plugin/plugin.json")
            claude_manifest = read_json(plugin_root / ".claude-plugin/plugin.json")

            self.assertEqual(
                plugin["source"],
                {"source": "local", "path": f"./plugins/{name}"},
            )
            self.assertEqual(plugin["policy"]["installation"], "AVAILABLE")
            self.assertEqual(codex_manifest["name"], name)
            self.assertEqual(claude_manifest["name"], name)
            self.assertEqual(codex_manifest["version"], claude_manifest["version"])

    def test_claude_sources_are_local_plugin_directories(self) -> None:
        for plugin in self.claude["plugins"]:
            self.assertEqual(plugin["source"], f"./plugins/{plugin['name']}")

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
