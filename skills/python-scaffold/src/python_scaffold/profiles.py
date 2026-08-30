import os
from collections.abc import Mapping
from copy import deepcopy
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any, get_args

import yaml
from mergedeep import merge
from platformdirs import user_config_path

from python_scaffold.models import Preset, Profile

PRESETS = frozenset(get_args(Preset))
PROFILE_IDENTITY_FIELDS = frozenset({"profile_name", "preset", "schema_version"})


def resolve_profile(
    selector: str,
    *,
    overrides: Mapping[str, Any] | None = None,
    environment: Mapping[str, str] = os.environ,
    persist_missing: bool = True,
) -> Profile:
    identity_overrides = PROFILE_IDENTITY_FIELDS.intersection(overrides or {})
    if identity_overrides:
        fields = ", ".join(sorted(identity_overrides))
        raise ValueError(f"Per-run overrides cannot change profile identity: {fields}")

    path = Path(selector).expanduser()
    if _looks_like_path(selector):
        raw = _read_yaml(path)
    else:
        preset, profile_name = _parse_selector(selector)
        persistent_path = profile_directory(environment) / f"{profile_name}.yaml"
        if not os.path.lexists(persistent_path):
            raw = load_bundled_preset(preset)
            raw["profile_name"] = profile_name
            candidate = Profile.model_validate(_merge(raw, overrides or {}))
            if not persist_missing:
                return candidate
            if _create_profile_if_absent(raw, persistent_path):
                return candidate
        raw = _read_yaml(persistent_path)
        _require_profile_identity(raw, preset, profile_name)

    resolved = _merge(raw, overrides or {})
    return Profile.model_validate(resolved)


def profile_directory(environment: Mapping[str, str] = os.environ) -> Path:
    configured = environment.get("AGENT_KIT_CONFIG_DIR")
    root = Path(configured).expanduser() if configured else user_config_path("agent-kit")
    return root / "scaffolds/python"


def load_bundled_preset(preset: str) -> dict[str, Any]:
    if preset not in PRESETS:
        raise ValueError(f"Unknown Python scaffold preset: {preset}")
    defaults = _read_yaml(config_directory() / "defaults.yaml")
    overrides = _read_yaml(preset_directory() / f"{preset}.yaml")
    return _merge(defaults, overrides)


def _parse_selector(selector: str) -> tuple[str, str]:
    parts = selector.split(":")
    if len(parts) > 2 or not parts[0]:
        raise ValueError(f"Invalid profile selector: {selector}")
    preset = parts[0]
    if preset not in PRESETS:
        raise ValueError(f"Unknown Python scaffold preset: {preset}")
    profile_name = parts[1] if len(parts) == 2 else preset
    if not profile_name or any(character in profile_name for character in "/\\"):
        raise ValueError(f"Invalid profile name: {profile_name}")
    return preset, profile_name


def _create_profile_if_absent(raw: Mapping[str, Any], destination: Path) -> bool:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8") as file:
            yaml.safe_dump(dict(raw), file, sort_keys=False)
    except FileExistsError:
        return False
    return True


def _require_profile_identity(raw: Mapping[str, Any], preset: str, profile_name: str) -> None:
    if raw.get("preset") != preset or raw.get("profile_name") != profile_name:
        raise ValueError(f"Persisted profile does not match selector {preset}:{profile_name}")


def preset_directory() -> Traversable:
    return config_directory() / "presets"


def config_directory() -> Traversable:
    return files("python_scaffold") / "config"


def _looks_like_path(value: str) -> bool:
    return (
        "/" in value or "\\" in value or value.endswith((".yaml", ".yml")) or value.startswith(".")
    )


def _read_yaml(path: Path | Traversable) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        value = yaml.safe_load(file)
    if not isinstance(value, dict):
        raise ValueError(f"Profile must contain a YAML mapping: {path}")
    return value


def _merge(base: Mapping[str, Any], changes: Mapping[str, Any]) -> dict[str, Any]:
    merged = deepcopy(dict(base))
    merge(merged, deepcopy(dict(changes)))
    return merged
