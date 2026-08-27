from typing import Any

import pytest

from python_scaffold.planner import Contribution, PlanningError, compose


def test_contributions_are_composed_deterministically() -> None:
    plan = compose(
        [
            Contribution(
                provider="ruff",
                dev_dependencies=("ruff>=0.15",),
                commands={"lint": ("ruff", "check", ".")},
            ),
            Contribution(
                provider="pytest",
                dev_dependencies=("pytest>=9",),
                files={"tests/test_smoke.py": "def test_smoke():\n    assert True\n"},
            ),
        ]
    )

    assert plan.dev_dependencies == ("pytest>=9", "ruff>=0.15")
    assert list(plan.commands) == ["lint"]
    assert list(plan.files) == ["tests/test_smoke.py"]


@pytest.mark.parametrize(
    ("left", "right", "message"),
    [
        (
            Contribution(provider="one", files={"pyproject.toml": "one"}),
            Contribution(provider="two", files={"pyproject.toml": "two"}),
            "file path pyproject.toml",
        ),
        (
            Contribution(provider="one", commands={"lint": ("ruff", "check")}),
            Contribution(provider="two", commands={"lint": ("pylint",)}),
            "command lint",
        ),
        (
            Contribution(provider="one", responsibilities=("general-lint",)),
            Contribution(provider="two", responsibilities=("general-lint",)),
            "responsibility general-lint",
        ),
        (
            Contribution(provider="one", dependencies=("demo<2",)),
            Contribution(provider="two", dependencies=("demo>=2",)),
            "dependency demo",
        ),
    ],
)
def test_collisions_fail_before_rendering(
    left: Contribution, right: Contribution, message: str
) -> None:
    with pytest.raises(PlanningError, match=message):
        compose([left, right])


@pytest.mark.parametrize(
    "path",
    [".", "../owned", "/tmp/owned", "a/../owned", "./pyproject.toml", "C:/owned", "C:owned"],
)
def test_provider_files_must_use_normalized_relative_paths(path: str) -> None:
    contribution = Contribution(provider="unsafe", files={path: "owned"})

    with pytest.raises(PlanningError, match="normalized relative path"):
        compose([contribution])


def test_dependency_cannot_be_owned_by_runtime_and_development_groups() -> None:
    contribution = Contribution(
        provider="confused",
        dependencies=("demo>=2",),
        dev_dependencies=("demo<2",),
    )

    with pytest.raises(PlanningError, match="dependency demo"):
        compose([contribution])


def test_composed_plan_mappings_are_immutable() -> None:
    plan = compose(
        [
            Contribution(
                provider="one",
                files={"README.md": "content"},
                commands={"lint": ("ruff", "check")},
            )
        ]
    )
    mutable_files: Any = plan.files
    mutable_commands: Any = plan.commands

    with pytest.raises(TypeError):
        mutable_files["owned.txt"] = "owned"
    with pytest.raises(TypeError):
        mutable_commands["test"] = ("pytest",)
