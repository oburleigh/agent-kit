import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from python_scaffold.models import Profile
from python_scaffold.profiles import PRESETS, load_bundled_preset

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("preset", sorted(PRESETS))
def test_bundled_presets_validate(preset: str) -> None:
    profile = Profile.model_validate(load_bundled_preset(preset))

    assert profile.preset == preset


def test_exported_schema_matches_the_model() -> None:
    exported = json.loads((ROOT / "src/python_scaffold/config/schema.json").read_text())

    assert exported == Profile.model_json_schema()


@pytest.mark.parametrize(
    ("preset", "changes", "message"),
    [
        ("library", {"http": "fastapi"}, "HTTP providers are limited to services"),
        ("service", {"http": "none"}, "A service requires FastAPI or Flask"),
        ("service", {"http": "fastapi", "runtime_validation": "none"}, "FastAPI requires Pydantic"),
        ("cli", {"cli": "none"}, "A CLI requires Click or Typer"),
        ("library", {"publishing": "pypi", "hooks": "none"}, "Commitizen requires a hook provider"),
    ],
)
def test_incompatible_profiles_are_rejected(
    preset: str, changes: dict[str, str], message: str
) -> None:
    raw = load_bundled_preset(preset)
    raw["providers"].update(changes)

    with pytest.raises(ValidationError, match=message):
        Profile.model_validate(raw)


@pytest.mark.parametrize(
    "member",
    [".", "../owned", "/tmp/owned", "a/../owned", "./package", "C:/owned", "C:owned"],
)
def test_workspace_members_must_be_normalized_relative_paths(member: str) -> None:
    raw = load_bundled_preset("workspace")
    raw["project"]["workspace_members"] = [member]

    with pytest.raises(ValidationError, match="normalized relative path"):
        Profile.model_validate(raw)
