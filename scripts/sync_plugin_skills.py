import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
PLUGINS = ROOT / "plugins"
IGNORED = shutil.ignore_patterns(
    ".coverage",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "htmlcov",
    "node_modules",
    "*.tar.gz",
    "*.whl",
)


def main() -> None:
    for source in sorted(SKILLS.iterdir()):
        if not (source / "SKILL.md").is_file():
            continue
        plugin = PLUGINS / source.name
        if not (plugin / ".codex-plugin/plugin.json").is_file():
            raise FileNotFoundError(f"Missing standalone plugin for {source.name}")
        destination = plugin / "skills" / source.name
        if destination.exists():
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, destination, ignore=IGNORED)


if __name__ == "__main__":
    main()
