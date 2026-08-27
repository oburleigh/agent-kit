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
