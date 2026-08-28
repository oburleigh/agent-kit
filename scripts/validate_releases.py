import json
import re
import sys
from pathlib import Path


SEMVER = re.compile(
    r"^(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
RUNTIME_VERSION_FILES = {
    ("json", ".codex-plugin/plugin.json", "$.version"),
    ("json", ".claude-plugin/plugin.json", "$.version"),
}
RELEASE_PLEASE_SCHEMA = (
    "https://raw.githubusercontent.com/googleapis/release-please/"
    "v17.6.0/schemas/config.json"
)
BOOTSTRAP_SHA = "a3423d74169d6b1f497399b9cc2a33783800d697"


def read_json(path: Path, errors: list[str], label: str) -> object | None:
    try:
        with path.open(encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        errors.append(f"missing {label}: {path.relative_to(path.parents[1])}")
    except (json.JSONDecodeError, OSError) as error:
        errors.append(f"invalid {label}: {error}")
    return None


def component_paths(names: set[str]) -> dict[str, str]:
    return {
        ("." if name == "agent-kit" else f"plugins/{name}"): name
        for name in sorted(names)
    }


def compare_component_sets(
    label: str, expected: set[str], actual: set[str], errors: list[str]
) -> None:
    differences = [
        *(f"missing {path}" for path in sorted(expected - actual)),
        *(f"unexpected {path}" for path in sorted(actual - expected)),
    ]
    if differences:
        errors.append(f"{label} components differ: {', '.join(differences)}")


def manifest_version(path: Path, errors: list[str], label: str) -> str:
    value = read_json(path, errors, label)
    if not isinstance(value, dict) or not isinstance(value.get("version"), str):
        return "<missing>"
    return value["version"]


def text_version(path: Path, errors: list[str], label: str) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError as error:
        errors.append(f"invalid {label}: {error}")
        return "<missing>"


def marketplace_names(value: object) -> set[str]:
    if not isinstance(value, dict) or not isinstance(value.get("plugins"), list):
        return set()
    return {
        plugin["name"]
        for plugin in value["plugins"]
        if isinstance(plugin, dict) and isinstance(plugin.get("name"), str)
    }


def validate_release_configuration(root: Path) -> list[str]:
    errors: list[str] = []
    codex_marketplace = read_json(
        root / ".agents/plugins/marketplace.json", errors, "Codex marketplace"
    )
    claude_marketplace = read_json(
        root / ".claude-plugin/marketplace.json", errors, "Claude marketplace"
    )
    codex_names = marketplace_names(codex_marketplace)
    claude_names = marketplace_names(claude_marketplace)
    if codex_names != claude_names:
        errors.append("Codex and Claude marketplaces publish different components")

    components = component_paths(codex_names | claude_names)
    expected_paths = set(components)
    release_manifest_value = read_json(
        root / ".release-please-manifest.json", errors, "release manifest"
    )
    release_manifest = (
        release_manifest_value if isinstance(release_manifest_value, dict) else {}
    )
    compare_component_sets(
        "release manifest", expected_paths, set(release_manifest), errors
    )

    config_value = read_json(
        root / "release-please-config.json", errors, "release config"
    )
    config = config_value if isinstance(config_value, dict) else {}
    packages_value = config.get("packages")
    packages = packages_value if isinstance(packages_value, dict) else {}
    compare_component_sets("release config", expected_paths, set(packages), errors)

    required_global_values = {
        "always-update": True,
        "include-component-in-tag": True,
        "include-v-in-tag": True,
        "tag-separator": "-",
        "separate-pull-requests": False,
        "bump-minor-pre-major": True,
        "bump-patch-for-minor-pre-major": True,
    }
    for key, expected in required_global_values.items():
        if config.get(key) != expected:
            errors.append(f"release config {key} must be {str(expected).lower()}")

    if config.get("$schema") != RELEASE_PLEASE_SCHEMA:
        errors.append("release config schema must target release-please v17.6.0")
    bootstrap_sha = config.get("bootstrap-sha")
    if bootstrap_sha != BOOTSTRAP_SHA:
        errors.append(
            f"release config bootstrap-sha must be the ADM-188 boundary {BOOTSTRAP_SHA}"
        )

    plugins = config.get("plugins", [])
    if isinstance(plugins, list) and any(
        isinstance(plugin, dict) and plugin.get("type") == "linked-versions"
        for plugin in plugins
    ):
        errors.append("release config must not link component versions")

    for component_path, name in components.items():
        component_root = root if component_path == "." else root / component_path
        release_version = release_manifest.get(component_path, "<missing>")
        version_file = text_version(
            component_root / "version.txt", errors, f"{name} version.txt"
        )
        codex_version = manifest_version(
            component_root / ".codex-plugin/plugin.json",
            errors,
            f"{name} Codex manifest",
        )
        claude_version = manifest_version(
            component_root / ".claude-plugin/plugin.json",
            errors,
            f"{name} Claude manifest",
        )
        versions = [release_version, version_file, codex_version, claude_version]
        if len(set(versions)) != 1:
            errors.append(
                f"{name} version drift: release={release_version}, "
                f"version.txt={version_file}, codex={codex_version}, "
                f"claude={claude_version}"
            )
        elif not isinstance(release_version, str) or not SEMVER.fullmatch(
            release_version
        ):
            errors.append(f"{name} version is not Semantic Versioning: {release_version}")

        if not (component_root / "CHANGELOG.md").is_file():
            errors.append(f"{name} is missing CHANGELOG.md")

        package_value = packages.get(component_path)
        package = package_value if isinstance(package_value, dict) else {}
        if package.get("component") != name:
            errors.append(f"{name} component name must be {name}")
        if package.get("release-type") != "simple":
            errors.append(f"{name} release-type must be simple")
        if package.get("version-file") != "version.txt":
            errors.append(f"{name} version-file must be version.txt")
        if package.get("changelog-path") != "CHANGELOG.md":
            errors.append(f"{name} changelog-path must be CHANGELOG.md")

        extra_files = package.get("extra-files")
        actual_extra_files = {
            (entry.get("type"), entry.get("path"), entry.get("jsonpath"))
            for entry in extra_files
            if isinstance(entry, dict)
        } if isinstance(extra_files, list) else set()
        if actual_extra_files != RUNTIME_VERSION_FILES:
            errors.append(
                f"{name} extra-files must target both runtime manifest versions"
            )

    return errors


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    root = Path(arguments[0]).resolve() if arguments else Path(__file__).parents[1]
    errors = validate_release_configuration(root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
