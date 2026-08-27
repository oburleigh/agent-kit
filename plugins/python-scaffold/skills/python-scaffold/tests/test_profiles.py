from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from python_scaffold.profiles import load_bundled_preset, resolve_profile


def test_named_profile_is_created_once(tmp_path: Path) -> None:
    environment = {"AGENT_KIT_CONFIG_DIR": str(tmp_path / "config")}

    first = resolve_profile("library:team", environment=environment)
    profile_path = tmp_path / "config/scaffolds/python/team.yaml"
    profile_path.write_text(profile_path.read_text().replace("Python library", "Team library"))
    second = resolve_profile("library:team", environment=environment)

    assert first.project.description == "Python library"
    assert second.project.description == "Team library"


def test_per_run_overrides_do_not_change_the_persistent_profile(tmp_path: Path) -> None:
    environment = {"AGENT_KIT_CONFIG_DIR": str(tmp_path / "config")}
    resolve_profile("service:api", environment=environment)
    profile_path = tmp_path / "config/scaffolds/python/api.yaml"
    before = yaml.safe_load(profile_path.read_text())

    resolved = resolve_profile(
        "service:api",
        overrides={"project": {"name": "orders-api"}},
        environment=environment,
    )

    assert resolved.project.name == "orders-api"
    assert yaml.safe_load(profile_path.read_text()) == before


def test_profile_path_is_loaded_without_creating_a_persistent_profile(tmp_path: Path) -> None:
    source = tmp_path / "complete.yaml"
    source.write_text(yaml.safe_dump(load_bundled_preset("cli"), sort_keys=False))
    environment = {"AGENT_KIT_CONFIG_DIR": str(tmp_path / "config")}

    resolved = resolve_profile(str(source), environment=environment)

    assert resolved.preset == "cli"
    assert not (tmp_path / "config").exists()


def test_invalid_first_run_override_does_not_create_a_profile(tmp_path: Path) -> None:
    environment = {"AGENT_KIT_CONFIG_DIR": str(tmp_path / "config")}

    with pytest.raises(ValidationError, match="A service requires FastAPI or Flask"):
        resolve_profile(
            "service:invalid",
            overrides={"providers": {"http": "none"}},
            environment=environment,
        )

    assert not (tmp_path / "config").exists()


@pytest.mark.parametrize(
    ("field", "value"),
    [("profile_name", "other"), ("preset", "service"), ("schema_version", 2)],
)
def test_per_run_overrides_cannot_change_profile_identity(
    tmp_path: Path, field: str, value: str | int
) -> None:
    environment = {"AGENT_KIT_CONFIG_DIR": str(tmp_path / "config")}

    with pytest.raises(ValueError, match="cannot change profile identity"):
        resolve_profile("library:team", overrides={field: value}, environment=environment)

    assert not (tmp_path / "config").exists()


@pytest.mark.parametrize(("field", "value"), [("profile_name", "other"), ("preset", "cli")])
def test_persisted_profile_must_match_its_selector(tmp_path: Path, field: str, value: str) -> None:
    environment = {"AGENT_KIT_CONFIG_DIR": str(tmp_path / "config")}
    resolve_profile("library:team", environment=environment)
    profile_path = tmp_path / "config/scaffolds/python/team.yaml"
    raw = yaml.safe_load(profile_path.read_text())
    raw[field] = value
    profile_path.write_text(yaml.safe_dump(raw, sort_keys=False))

    with pytest.raises(ValueError, match="does not match selector"):
        resolve_profile("library:team", environment=environment)
