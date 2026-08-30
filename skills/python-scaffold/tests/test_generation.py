import os
import subprocess
import tomllib
from pathlib import Path

import pytest

from python_scaffold.generate import generate_repository
from python_scaffold.profiles import load_bundled_preset


@pytest.mark.parametrize(
    ("preset", "expected_source"),
    [
        ("cli", "src/python_cli/cli.py"),
        ("library", "src/python_library/__init__.py"),
        ("service", "src/python_service/app.py"),
        ("workspace", "apps/app/pyproject.toml"),
    ],
)
def test_presets_generate_complete_repositories(
    tmp_path: Path, preset: str, expected_source: str
) -> None:
    raw = load_bundled_preset(preset)
    raw["execution"] = {
        "install_dependencies": False,
        "run_quality_gates": False,
        "initialize_git": False,
    }
    target = tmp_path / preset

    generate_repository(raw, target)

    expected_baseline = {
        ".gitignore",
        "AGENTS.md",
        "CONTRIBUTING.md",
        "LICENSE",
        "README.md",
        "SECURITY.md",
        "docs/coding-standards.md",
        "pyproject.toml",
    }
    assert expected_baseline <= {
        path.relative_to(target).as_posix() for path in target.rglob("*") if path.is_file()
    }
    assert (target / expected_source).is_file()


@pytest.mark.parametrize("preset", ["cli", "library", "service", "workspace"])
def test_generated_python_is_ruff_formatted(tmp_path: Path, preset: str) -> None:
    raw = load_bundled_preset(preset)
    raw["execution"] = {
        "install_dependencies": False,
        "run_quality_gates": False,
        "initialize_git": False,
    }
    target = tmp_path / preset
    generate_repository(raw, target)

    subprocess.run(["ruff", "format", "--check", "."], cwd=target, check=True)


@pytest.mark.parametrize("preset", ["cli", "library", "service", "workspace"])
def test_generated_python_passes_ruff_lint(tmp_path: Path, preset: str) -> None:
    raw = load_bundled_preset(preset)
    raw["execution"] = {
        "install_dependencies": False,
        "run_quality_gates": False,
        "initialize_git": False,
    }
    target = tmp_path / preset
    generate_repository(raw, target)

    subprocess.run(["ruff", "check", "."], cwd=target, check=True)


def test_service_uses_fastapi_pydantic_and_working_test_configuration(tmp_path: Path) -> None:
    raw = load_bundled_preset("service")
    raw["project"].update({"name": "orders-api", "description": "Orders API"})
    raw["execution"] = {
        "install_dependencies": False,
        "run_quality_gates": False,
        "initialize_git": False,
    }
    target = tmp_path / "orders-api"

    generate_repository(raw, target)

    pyproject = tomllib.loads((target / "pyproject.toml").read_text())
    dependencies = "\n".join(pyproject["project"]["dependencies"])
    dev_dependencies = "\n".join(pyproject["dependency-groups"]["dev"])
    assert "fastapi" in dependencies
    assert "pydantic" in dependencies
    assert "structlog" in dependencies
    assert "httpx2" in dev_dependencies
    assert pyproject["tool"]["coverage"]["report"]["fail_under"] == 80
    assert (target / "tests/integration/test_health.py").is_file()
    app_source = (target / "src/orders_api/app.py").read_text()
    assert "BaseModel" in app_source
    assert "structlog" in app_source


def test_cli_provider_generates_a_unit_test(tmp_path: Path) -> None:
    raw = load_bundled_preset("cli")
    raw["execution"] = {
        "install_dependencies": False,
        "run_quality_gates": False,
        "initialize_git": False,
    }
    target = tmp_path / "cli"

    generate_repository(raw, target)

    assert (target / "tests/unit/test_cli.py").is_file()
    pyproject = tomllib.loads((target / "pyproject.toml").read_text())
    assert any(
        dependency.startswith("click") for dependency in pyproject["project"]["dependencies"]
    )


@pytest.mark.parametrize("preset", ["cli", "library", "service", "workspace"])
def test_unittest_provider_generates_unittest_cases(tmp_path: Path, preset: str) -> None:
    raw = load_bundled_preset(preset)
    raw["providers"]["tests"] = "unittest"
    raw["execution"] = {
        "install_dependencies": False,
        "run_quality_gates": False,
        "initialize_git": False,
    }
    target = tmp_path / preset

    generate_repository(raw, target)

    tests = list(target.rglob("test_*.py"))
    assert tests
    assert all("unittest.TestCase" in test.read_text() for test in tests)


def test_unittest_discovers_generated_library_tests(tmp_path: Path) -> None:
    raw = load_bundled_preset("library")
    raw["providers"]["tests"] = "unittest"
    raw["execution"] = {
        "install_dependencies": False,
        "run_quality_gates": False,
        "initialize_git": False,
    }
    target = tmp_path / "library"
    generate_repository(raw, target)

    subprocess.run(
        ["python", "-m", "unittest", "discover", "-s", "tests"],
        cwd=target,
        env={**os.environ, "PYTHONPATH": str(target / "src")},
        check=True,
    )


def test_unittest_quality_gates_enforce_the_coverage_threshold(tmp_path: Path) -> None:
    raw = load_bundled_preset("library")
    raw["providers"]["tests"] = "unittest"
    raw["execution"] = {
        "install_dependencies": False,
        "run_quality_gates": False,
        "initialize_git": False,
    }
    target = tmp_path / "library"

    generate_repository(raw, target)

    pyproject = tomllib.loads((target / "pyproject.toml").read_text())
    commands = pyproject["tool"]["agent-kit"]["commands"]
    assert commands["test"] == [
        "uv",
        "run",
        "coverage",
        "run",
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
    ]
    assert commands["coverage"] == ["uv", "run", "coverage", "report"]


def test_workspace_unittest_commands_cover_each_member(tmp_path: Path) -> None:
    raw = load_bundled_preset("workspace")
    raw["providers"]["tests"] = "unittest"
    raw["execution"] = {
        "install_dependencies": False,
        "run_quality_gates": False,
        "initialize_git": False,
    }
    target = tmp_path / "workspace"

    generate_repository(raw, target)

    pyproject = tomllib.loads((target / "pyproject.toml").read_text())
    commands = pyproject["tool"]["agent-kit"]["commands"]
    assert commands["test-app"][-1] == "apps/app/tests"
    assert commands["test-core"][4] == "--append"
    assert commands["test-core"][-1] == "packages/core/tests"
    assert commands["coverage"] == ["uv", "run", "coverage", "report"]


@pytest.mark.parametrize("preset", ["cli", "library", "service", "workspace"])
def test_tests_none_generates_no_test_files(tmp_path: Path, preset: str) -> None:
    raw = load_bundled_preset(preset)
    raw["providers"]["tests"] = "none"
    raw["tools"]["test_tiers"] = []
    raw["execution"] = {
        "install_dependencies": False,
        "run_quality_gates": False,
        "initialize_git": False,
    }
    target = tmp_path / preset

    generate_repository(raw, target)

    assert not list(target.rglob("test_*.py"))


def test_hook_configuration_uses_only_selected_providers(tmp_path: Path) -> None:
    raw = load_bundled_preset("service")
    raw["providers"].update(
        {
            "commit_lint": "none",
            "hooks": "pre-commit",
            "quality": "none",
            "tests": "unittest",
        }
    )
    raw["execution"] = {
        "install_dependencies": False,
        "run_quality_gates": False,
        "initialize_git": False,
    }
    target = tmp_path / "service"

    generate_repository(raw, target)

    hooks = (target / ".pre-commit-config.yaml").read_text()
    assert "ruff" not in hooks
    assert "pytest" not in hooks
    assert "commitizen" not in hooks
    assert "coverage run -m unittest" in hooks


def test_alternate_providers_generate_their_owned_configuration(tmp_path: Path) -> None:
    raw = load_bundled_preset("service")
    raw["providers"].update(
        {
            "build_backend": "hatchling",
            "ci": "gitlab-ci",
            "hooks": "lefthook",
            "http": "flask",
            "logging": "standard-library",
            "runtime_validation": "none",
            "tests": "unittest",
            "type_checker": "mypy",
        }
    )
    raw["execution"] = {
        "install_dependencies": False,
        "run_quality_gates": False,
        "initialize_git": False,
    }
    target = tmp_path / "flask-service"

    generate_repository(raw, target)

    pyproject = tomllib.loads((target / "pyproject.toml").read_text())
    dependencies = "\n".join(pyproject["project"]["dependencies"])
    dev_dependencies = "\n".join(pyproject["dependency-groups"]["dev"])
    assert "flask" in dependencies.lower()
    assert "mypy" in dev_dependencies
    assert (target / ".gitlab-ci.yml").is_file()
    assert (target / "lefthook.yml").is_file()
    assert pyproject["build-system"]["build-backend"] == "hatchling.build"


def test_ci_and_readme_use_only_selected_provider_commands(tmp_path: Path) -> None:
    raw = load_bundled_preset("service")
    raw["providers"].update(
        {
            "architecture": "none",
            "ci": "github-actions",
            "duplication": "none",
            "quality": "none",
            "secret_scan": "none",
            "tests": "unittest",
            "type_checker": "mypy",
        }
    )
    raw["execution"] = {
        "install_dependencies": False,
        "run_quality_gates": False,
        "initialize_git": False,
    }
    target = tmp_path / "minimal-service"

    generate_repository(raw, target)

    ci = (target / ".github/workflows/ci.yml").read_text()
    readme = (target / "README.md").read_text()
    assert "ruff" not in ci
    assert "pytest" not in ci
    assert "uv run mypy src tests" in ci
    assert "uv run coverage run -m unittest discover -s tests" in ci
    assert "ruff" not in readme
    assert "pytest" not in readme


def test_workspace_root_is_not_built_as_a_missing_package(tmp_path: Path) -> None:
    raw = load_bundled_preset("workspace")
    raw["execution"] = {
        "install_dependencies": False,
        "run_quality_gates": False,
        "initialize_git": False,
    }
    target = tmp_path / "workspace"

    generate_repository(raw, target)

    pyproject = tomllib.loads((target / "pyproject.toml").read_text())
    assert "build-system" not in pyproject
    assert pyproject["tool"]["uv"]["package"] is False
    commands = pyproject["tool"]["agent-kit"]["commands"]
    assert "build" not in commands
    assert commands["duplication"] == ["uv", "run", "pylint", "apps", "packages"]
    assert commands["typecheck"] == ["uv", "run", "ty", "check", "apps", "packages"]


def test_workspace_member_tests_collect_without_module_collisions(tmp_path: Path) -> None:
    raw = load_bundled_preset("workspace")
    raw["execution"] = {
        "install_dependencies": False,
        "run_quality_gates": False,
        "initialize_git": False,
    }
    target = tmp_path / "workspace"
    generate_repository(raw, target)

    subprocess.run(["pytest", "--collect-only", "-q"], cwd=target, check=True)


def test_apache_license_contains_the_complete_terms(tmp_path: Path) -> None:
    raw = load_bundled_preset("library")
    raw["execution"] = {
        "install_dependencies": False,
        "run_quality_gates": False,
        "initialize_git": False,
    }
    target = tmp_path / "library"

    generate_repository(raw, target)

    license_text = (target / "LICENSE").read_text()
    pyproject = tomllib.loads((target / "pyproject.toml").read_text())
    assert pyproject["project"]["license"] == "Apache-2.0"
    assert "TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION" in license_text
    assert "END OF TERMS AND CONDITIONS" in license_text


def test_selected_execution_steps_run_before_git_initialization(tmp_path: Path) -> None:
    raw = load_bundled_preset("library")
    target = tmp_path / "library"
    calls: list[tuple[tuple[str, ...], Path]] = []

    def run(command: tuple[str, ...], cwd: Path) -> None:
        calls.append((command, cwd))

    generate_repository(raw, target, run_command=run)

    assert calls[0][0] == ("uv", "sync", "--all-groups")
    commands = [command for command, _ in calls]
    assert ("git", "init", "--initial-branch=main") in commands
    assert len({cwd for _, cwd in calls}) == 1
    assert calls[0][1].name.startswith(".library-")
    assert ("uv", "run", "ruff", "check", ".") in commands
    assert ("uv", "run", "pytest") in commands


def test_default_commands_use_concise_logged_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    raw = load_bundled_preset("library")
    raw["execution"] = {
        "install_dependencies": False,
        "run_quality_gates": False,
        "initialize_git": True,
    }
    log_root = tmp_path / "logs"
    monkeypatch.setenv("AGENT_KIT_LOG_DIR", str(log_root))

    generate_repository(raw, tmp_path / "logged")

    output = capsys.readouterr().out.splitlines()
    assert output[0] == "PASS git init --initial-branch=main"
    assert output[1].startswith("Full command logs: ")
    sessions = list((log_root / "scaffolds/python").iterdir())
    assert len(sessions) == 1
    assert "$ git init --initial-branch=main" in (sessions[0] / "commands.log").read_text()


def test_lefthook_is_installed_after_git_initialization(tmp_path: Path) -> None:
    raw = load_bundled_preset("library")
    raw["providers"]["hooks"] = "lefthook"
    target = tmp_path / "library"
    calls: list[tuple[str, ...]] = []

    def run(command: tuple[str, ...], _cwd: Path) -> None:
        calls.append(command)

    generate_repository(raw, target, run_command=run)

    git_index = calls.index(("git", "init", "--initial-branch=main"))
    lefthook_index = calls.index(("lefthook", "install"))
    assert lefthook_index > git_index


def test_generated_repository_is_initialized_when_enabled(tmp_path: Path) -> None:
    raw = load_bundled_preset("library")
    raw["execution"]["install_dependencies"] = False
    raw["execution"]["run_quality_gates"] = False
    target = tmp_path / "library"

    generate_repository(raw, target)

    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=target,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert branch == "main"


def test_generated_standards_are_package_first_and_reject_commentary_history(
    tmp_path: Path,
) -> None:
    raw = load_bundled_preset("library")
    raw["execution"] = {
        "install_dependencies": False,
        "run_quality_gates": False,
        "initialize_git": False,
    }
    target = tmp_path / "library"

    generate_repository(raw, target)

    standards = (target / "docs/coding-standards.md").read_text()
    agents = (target / "AGENTS.md").read_text()
    assert "maintained package" in standards
    assert "why the code exists" in agents
    assert "change history" in agents


@pytest.mark.parametrize("preset", ["cli", "library", "service", "workspace"])
def test_default_preset_passes_selected_gates(tmp_path: Path, preset: str) -> None:
    raw = load_bundled_preset(preset)
    raw["providers"]["secret_scan"] = "none"
    raw["execution"]["initialize_git"] = False

    generate_repository(raw, tmp_path / preset)


def test_click_setuptools_pyright_stack_passes_selected_gates(tmp_path: Path) -> None:
    raw = load_bundled_preset("cli")
    raw["providers"].update(
        {
            "build_backend": "setuptools",
            "cli": "click",
            "hooks": "lefthook",
            "secret_scan": "none",
            "type_checker": "pyright",
        }
    )
    raw["execution"]["initialize_git"] = False

    target = tmp_path / "click-cli"
    generate_repository(raw, target)

    assert (target / ".git").exists() is False
    assert (target / "lefthook.yml").is_file()


def test_flask_hatchling_mypy_unittest_stack_passes_selected_gates(
    tmp_path: Path,
) -> None:
    raw = load_bundled_preset("service")
    raw["providers"].update(
        {
            "build_backend": "hatchling",
            "ci": "gitlab-ci",
            "hooks": "lefthook",
            "http": "flask",
            "logging": "standard-library",
            "runtime_validation": "none",
            "secret_scan": "none",
            "tests": "unittest",
            "type_checker": "mypy",
        }
    )
    raw["execution"]["initialize_git"] = False

    target = tmp_path / "flask-service"
    generate_repository(raw, target)

    assert (target / ".gitlab-ci.yml").is_file()


def test_generated_gates_reject_lint_type_coverage_commit_and_pre_push_mutations(
    tmp_path: Path,
) -> None:
    raw = load_bundled_preset("library")
    raw["providers"]["secret_scan"] = "none"
    raw["execution"]["run_quality_gates"] = False
    target = tmp_path / "mutation-probes"
    generate_repository(raw, target)

    module = target / "src/python_library"

    lint_violation = module / "lint_violation.py"
    lint_violation.write_text("import os\n")
    _assert_command_fails(target, "uv", "run", "ruff", "check", ".")
    lint_violation.unlink()

    type_violation = module / "type_violation.py"
    type_violation.write_text('value: int = "wrong"\n')
    _assert_command_fails(target, "uv", "run", "ty", "check", "src", "tests")
    type_violation.unlink()

    uncovered = module / "uncovered.py"
    uncovered.write_text(
        "def branch(value: bool) -> int:\n    if value:\n        return 1\n    return 0\n"
    )
    _assert_command_fails(target, "uv", "run", "pytest")
    uncovered.unlink()

    message = target / "bad-message.txt"
    message.write_text("not a conventional commit\n")
    _assert_command_fails(
        target,
        "uv",
        "run",
        "pre-commit",
        "run",
        "commitizen",
        "--hook-stage",
        "commit-msg",
        "--commit-msg-filename",
        str(message),
    )

    test_file = target / "tests/unit/test_library.py"
    original_test = test_file.read_text()
    test_file.write_text(original_test.replace('"Hello, Ada!"', '"Wrong"'))
    _assert_command_fails(
        target,
        "uv",
        "run",
        "pre-commit",
        "run",
        "tests",
        "--hook-stage",
        "pre-push",
        "--all-files",
    )


def _assert_command_fails(target: Path, *command: str) -> None:
    result = subprocess.run(command, cwd=target, check=False, capture_output=True, text=True)
    assert result.returncode != 0, result.stdout + result.stderr
