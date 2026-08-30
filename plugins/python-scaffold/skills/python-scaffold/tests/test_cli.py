import json
from pathlib import Path

from typer.testing import CliRunner

from python_scaffold.cli import app


def test_cli_creates_a_repository_from_a_preset(tmp_path: Path) -> None:
    target = tmp_path / "example"
    config = tmp_path / "config"
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "--profile",
            "library:test",
            "--target",
            str(target),
            "--name",
            "example",
            "--description",
            "Example library",
            "--author",
            "Example Maintainer",
            "--no-install",
            "--no-check",
            "--no-git",
        ],
        env={"AGENT_KIT_CONFIG_DIR": str(config)},
    )

    assert result.exit_code == 0, result.output
    assert (target / "pyproject.toml").is_file()
    assert (config / "scaffolds/python/test.yaml").is_file()


def test_cli_plans_without_creating_a_profile_or_target(tmp_path: Path) -> None:
    target = tmp_path / "planned-library"
    config = tmp_path / "config"
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "--profile",
            "library:efficient",
            "--target",
            str(target),
            "--name",
            "planned-library",
            "--description",
            "Planned Python library",
            "--author",
            "Example Maintainer",
            "--plan",
        ],
        env={"AGENT_KIT_CONFIG_DIR": str(config)},
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {
        "schema_version": 1,
        "target": str(target),
        "preset": "library",
        "project": {
            "name": "planned-library",
            "description": "Planned Python library",
            "author": "Example Maintainer",
            "repository_url": None,
            "python_version": "3.14",
        },
        "selected_providers": {
            "build_backend": "uv-build",
            "ci": "github-actions",
            "commit_lint": "commitizen",
            "dependency_audit": "pip-audit",
            "duplication": "pylint",
            "hooks": "pre-commit",
            "license": "apache-2.0",
            "logging": "standard-library",
            "publishing": "pypi",
            "quality": "ruff",
            "secret_scan": "gitleaks",
            "tests": "pytest",
            "type_checker": "ty",
        },
        "disabled_providers": [
            "architecture",
            "cli",
            "http",
            "runtime_validation",
            "workspace",
        ],
        "workspace_members": [],
        "quality_gates": [
            "uv build",
            "uv run ruff format --check .",
            "uv run ruff check .",
            "uv run pytest",
            "uv run ty check src tests",
            "uv run pip-audit",
            "uv run pylint src",
            "gitleaks detect --source .",
        ],
        "execution": {
            "install_dependencies": True,
            "run_quality_gates": True,
            "initialize_git": True,
        },
    }
    assert not target.exists()
    assert not config.exists()
