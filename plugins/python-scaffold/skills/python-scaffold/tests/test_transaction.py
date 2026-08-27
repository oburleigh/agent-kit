from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from python_scaffold.core import generate_repository
from python_scaffold.models import Profile
from python_scaffold.profiles import load_bundled_preset
from python_scaffold.transaction import TargetExistsError, create_only


def test_existing_target_is_rejected_before_build_runs(tmp_path: Path) -> None:
    target = tmp_path / "owned"
    target.mkdir()
    called = False

    def build(_: Path) -> None:
        nonlocal called
        called = True

    with pytest.raises(TargetExistsError):
        create_only(target, build)

    assert not called


def test_dangling_target_symlink_is_treated_as_user_owned(tmp_path: Path) -> None:
    target = tmp_path / "owned-link"
    target.symlink_to(tmp_path / "missing")

    with pytest.raises(TargetExistsError):
        create_only(target, lambda _: None)

    assert target.is_symlink()


def test_failed_build_removes_only_its_staging_directory(tmp_path: Path) -> None:
    target = tmp_path / "new-project"
    owned = tmp_path / "owned.txt"
    owned.write_text("keep")

    def fail(staging: Path) -> None:
        (staging / "partial.txt").write_text("partial")
        raise RuntimeError("gate failed")

    with pytest.raises(RuntimeError, match="gate failed"):
        create_only(target, fail)

    assert not target.exists()
    assert owned.read_text() == "keep"
    assert list(tmp_path.glob(".new-project-*")) == []


def test_target_created_during_build_is_preserved(tmp_path: Path) -> None:
    target = tmp_path / "new-project"

    def build(staging: Path) -> None:
        (staging / "generated.txt").write_text("generated")
        target.mkdir()
        (target / "owned.txt").write_text("owned")

    with pytest.raises(TargetExistsError, match="created during generation"):
        create_only(target, build)

    assert (target / "owned.txt").read_text() == "owned"
    assert list(tmp_path.glob(".new-project-*")) == []


def test_success_atomically_moves_the_complete_staging_directory(tmp_path: Path) -> None:
    target = tmp_path / "new-project"

    def build(staging: Path) -> None:
        (staging / "ready.txt").write_text("ready")

    create_only(target, build)

    assert (target / "ready.txt").read_text() == "ready"
    assert list(tmp_path.glob(".new-project-*")) == []


def test_target_created_at_commit_is_not_replaced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "new-project"
    original_mkdir = Path.mkdir
    raced = False

    def race(path: Path, mode: int = 0o777, parents: bool = False, exist_ok: bool = False) -> None:
        nonlocal raced
        if path == target and not raced:
            raced = True
            original_mkdir(path)
        original_mkdir(path, mode=mode, parents=parents, exist_ok=exist_ok)

    monkeypatch.setattr(Path, "mkdir", race)

    def build(staging: Path) -> None:
        (staging / "ready.txt").write_text("ready")

    with pytest.raises(TargetExistsError, match="created during generation"):
        create_only(target, build)

    assert target.is_dir()
    assert list(target.iterdir()) == []
    assert list(tmp_path.glob(".new-project-*")) == []


def test_invalid_profile_fails_before_staging_is_created(tmp_path: Path) -> None:
    raw = load_bundled_preset("library")
    raw["providers"]["http"] = "fastapi"
    target = tmp_path / "new-project"

    def render(profile: object, plan: object, staging: Path) -> None:
        del profile, plan, staging

    with pytest.raises(ValidationError, match="HTTP providers are limited to services"):
        generate_repository(raw, target, [], render)

    assert not target.exists()
    assert list(tmp_path.glob(".new-project-*")) == []


def test_mutated_profile_instance_is_revalidated_before_staging(tmp_path: Path) -> None:
    profile = Profile.model_validate(load_bundled_preset("library"))
    mutable_commands: Any = profile.additions.commands
    mutable_commands["invalid"] = [1]
    target = tmp_path / "new-project"

    def render(profile: object, plan: object, staging: Path) -> None:
        del profile, plan, staging

    with pytest.raises(ValidationError, match="valid string"):
        generate_repository(profile, target, [], render)

    assert not target.exists()
    assert list(tmp_path.glob(".new-project-*")) == []


def test_profile_models_reject_attribute_mutation() -> None:
    profile = Profile.model_validate(load_bundled_preset("library"))
    mutable_project: Any = profile.project

    with pytest.raises(ValidationError, match="frozen"):
        mutable_project.name = "renamed"
