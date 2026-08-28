from importlib.resources import files
from typing import Any

import yaml

from python_scaffold.models import Profile
from python_scaffold.planner import Contribution, Plan, compose


def build_plan(profile: Profile) -> Plan:
    contributions = [
        _preset(profile),
        _build_backend(profile) if profile.preset != "workspace" else None,
        _quality(profile),
        _tests(profile),
        _type_checker(profile),
        _architecture(profile),
        _cli(profile),
        _commit_lint(profile),
        _dependency_audit(profile),
        _duplication(profile),
        _hooks(profile),
        _http(profile),
        _logging(profile),
        _publishing(profile),
        _runtime_validation(profile),
        _secret_scan(profile),
        _workspace(profile),
        _additions(profile),
    ]
    selected = [contribution for contribution in contributions if contribution is not None]
    project_plan = compose(selected)
    packaging = [_baseline(profile, project_plan)]
    ci = _ci(profile, project_plan)
    if ci is not None:
        packaging.append(ci)
    return compose([*selected, *packaging])


def package_requirement(name: str) -> str:
    catalog = _package_catalog()
    try:
        value = catalog[name]
    except KeyError as error:
        raise ValueError(f"No shipped package requirement for {name}") from error
    if not isinstance(value, str):
        raise ValueError(f"Invalid shipped package requirement for {name}")
    return value


def _package_catalog() -> dict[str, Any]:
    resource = files("python_scaffold") / "config/packages.yaml"
    with resource.open(encoding="utf-8") as file:
        value = yaml.safe_load(file)
    if not isinstance(value, dict):
        raise ValueError("Package catalog must contain a YAML mapping")
    return value


def _baseline(profile: Profile, plan: Plan) -> Contribution:
    return Contribution(
        provider="baseline",
        files={
            ".gitignore": _gitignore(),
            "AGENTS.md": _agents(),
            "CONTRIBUTING.md": _contributing(plan),
            "README.md": _readme(profile, plan),
            "SECURITY.md": _security(profile),
            "docs/coding-standards.md": _standards(),
        },
        responsibilities=("repository-documentation",),
    )


def _preset(profile: Profile) -> Contribution:
    module = _module_name(profile.project.name)
    if profile.preset == "library":
        generated = {
            f"src/{module}/__init__.py": (
                '"""Public package interface."""\n\n\n'
                "def greet(name: str) -> str:\n"
                '    return f"Hello, {name}!"\n'
            )
        }
        if profile.providers.tests != "none":
            generated.update(_test_package_files("tests/unit"))
            generated["tests/unit/test_library.py"] = _library_test(module, profile.providers.tests)
        return Contribution(
            provider="preset-library",
            files=generated,
            responsibilities=("project-source",),
        )
    if profile.preset == "service":
        return Contribution(
            provider="preset-service",
            files={f"src/{module}/__init__.py": '"""Service package."""\n'},
            responsibilities=("project-source",),
        )
    if profile.preset == "cli":
        return Contribution(
            provider="preset-cli",
            files={f"src/{module}/__init__.py": '"""CLI package."""\n'},
            responsibilities=("project-source",),
        )
    return Contribution(
        provider="preset-workspace",
        files={"packages/.gitkeep": "", "apps/.gitkeep": ""},
        responsibilities=("project-source",),
    )


def _build_backend(profile: Profile) -> Contribution:
    name = profile.providers.build_backend
    return Contribution(
        provider=f"build-{name}",
        dev_dependencies=(package_requirement(name),),
        commands={"build": ("uv", "build")},
        gates=(("uv", "build"),),
        responsibilities=("build",),
    )


def _quality(profile: Profile) -> Contribution | None:
    if profile.providers.quality == "none":
        return None
    return Contribution(
        provider="quality-ruff",
        dev_dependencies=(package_requirement("ruff"),),
        files={"ruff.toml": _ruff_config(profile)},
        commands={
            "format-check": ("uv", "run", "ruff", "format", "--check", "."),
            "lint": ("uv", "run", "ruff", "check", "."),
        },
        gates=(
            ("uv", "run", "ruff", "format", "--check", "."),
            ("uv", "run", "ruff", "check", "."),
        ),
        responsibilities=("format", "general-lint"),
    )


def _tests(profile: Profile) -> Contribution | None:
    provider = profile.providers.tests
    if provider == "none":
        return None
    common_files = {".coveragerc": _coverage_config(profile)}
    if provider == "pytest":
        return Contribution(
            provider="tests-pytest",
            dev_dependencies=(package_requirement("pytest"), package_requirement("pytest-cov")),
            files={**common_files, "pytest.ini": _pytest_config(profile)},
            commands={"test": ("uv", "run", "pytest")},
            gates=(("uv", "run", "pytest"),),
            responsibilities=("tests", "coverage"),
        )
    commands = _unittest_commands(profile)
    return Contribution(
        provider="tests-unittest",
        dev_dependencies=(package_requirement("coverage"),),
        files=common_files,
        commands=commands,
        gates=tuple(commands.values()),
        responsibilities=("tests", "coverage"),
    )


def _unittest_commands(profile: Profile) -> dict[str, tuple[str, ...]]:
    if profile.preset != "workspace":
        return {
            "test": (
                "uv",
                "run",
                "coverage",
                "run",
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests",
            ),
            "coverage": ("uv", "run", "coverage", "report"),
        }

    commands: dict[str, tuple[str, ...]] = {}
    for index, member in enumerate(profile.project.workspace_members):
        name = _module_name(member.rsplit("/", maxsplit=1)[-1])
        append = ("--append",) if index else ()
        commands[f"test-{name}"] = (
            "uv",
            "run",
            "coverage",
            "run",
            *append,
            "-m",
            "unittest",
            "discover",
            "-s",
            f"{member}/tests",
        )
    commands["coverage"] = ("uv", "run", "coverage", "report")
    return commands


def _type_checker(profile: Profile) -> Contribution | None:
    provider = profile.providers.type_checker
    if provider == "none":
        return None
    paths = ("apps", "packages") if profile.preset == "workspace" else ("src", "tests")
    include_json = ", ".join(f'"{path}"' for path in paths)
    include_toml = ", ".join(f'"{path}"' for path in paths)
    configurations = {
        "mypy": ("mypy.ini", "[mypy]\nstrict = True\nwarn_unreachable = True\n"),
        "pyright": (
            "pyrightconfig.json",
            f'{{\n  "typeCheckingMode": "strict",\n  "include": [{include_json}]\n}}\n',
        ),
        "ty": (
            "ty.toml",
            f'[environment]\npython-version = "3.14"\n\n[src]\ninclude = [{include_toml}]\n',
        ),
    }
    path, content = configurations[provider]
    command = {
        "mypy": ("uv", "run", "mypy", *paths),
        "pyright": ("uv", "run", "pyright", *paths),
        "ty": ("uv", "run", "ty", "check", *paths),
    }[provider]
    return Contribution(
        provider=f"types-{provider}",
        dev_dependencies=(package_requirement(provider),),
        files={path: content},
        commands={"typecheck": command},
        gates=(command,),
        responsibilities=("type-check",),
    )


def _architecture(profile: Profile) -> Contribution | None:
    if profile.providers.architecture == "none":
        return None
    module = _module_name(profile.project.name)
    return Contribution(
        provider="architecture-import-linter",
        dev_dependencies=(package_requirement("import-linter"),),
        files={
            ".importlinter": (
                "[importlinter]\n"
                f"root_package = {module}\n\n"
                "include_external_packages = True\n\n"
                "[importlinter:contract:no-tests-in-source]\n"
                "name = Source does not import tests\n"
                "type = forbidden\n"
                f"source_modules = {module}\n"
                "forbidden_modules = tests\n"
            )
        },
        commands={"architecture": ("uv", "run", "lint-imports")},
        gates=(("uv", "run", "lint-imports"),),
        responsibilities=("architecture",),
    )


def _ci(profile: Profile, plan: Plan) -> Contribution | None:
    provider = profile.providers.ci
    if provider == "none":
        return None
    if provider == "github-actions":
        return Contribution(
            provider="ci-github-actions",
            files={".github/workflows/ci.yml": _github_actions(profile, plan)},
            responsibilities=("ci",),
        )
    return Contribution(
        provider="ci-gitlab",
        files={".gitlab-ci.yml": _gitlab_ci(profile, plan)},
        responsibilities=("ci",),
    )


def _cli(profile: Profile) -> Contribution | None:
    provider = profile.providers.cli
    if provider == "none":
        return None
    module = _module_name(profile.project.name)
    if provider == "typer":
        content = (
            "import typer\n\n"
            "app = typer.Typer(no_args_is_help=True)\n\n\n"
            "@app.command()\n"
            'def hello(name: str = "world") -> None:\n'
            '    typer.echo(f"Hello, {name}!")\n'
        )
    else:
        content = (
            "import click\n\n\n"
            "@click.command()\n"
            '@click.option("--name", default="world")\n'
            "def app(name: str) -> None:\n"
            '    click.echo(f"Hello, {name}!")\n'
        )
    generated = {f"src/{module}/cli.py": content}
    if profile.providers.tests != "none":
        generated.update(_test_package_files("tests/unit"))
        generated["tests/unit/test_cli.py"] = _cli_test(module, provider, profile.providers.tests)
    return Contribution(
        provider=f"cli-{provider}",
        dependencies=(
            (package_requirement("click"), package_requirement("typer"))
            if provider == "typer"
            else (package_requirement("click"),)
        ),
        files=generated,
        commands={"run": ("uv", "run", profile.project.name)},
        responsibilities=("cli",),
    )


def _commit_lint(profile: Profile) -> Contribution | None:
    if profile.providers.commit_lint == "none":
        return None
    return Contribution(
        provider="commits-commitizen",
        dev_dependencies=(package_requirement("commitizen"),),
        files={
            ".cz.toml": (
                "[tool.commitizen]\n"
                'name = "cz_conventional_commits"\n'
                'tag_format = "v$version"\n'
                'version_provider = "pep621"\n'
            )
        },
        commands={"commit-check": ("uv", "run", "cz", "check", "--rev-range", "HEAD~1..HEAD")},
        responsibilities=("commit-message",),
    )


def _dependency_audit(profile: Profile) -> Contribution | None:
    if profile.providers.dependency_audit == "none":
        return None
    return Contribution(
        provider="audit-pip-audit",
        dev_dependencies=(package_requirement("pip-audit"),),
        commands={"audit": ("uv", "run", "pip-audit")},
        gates=(("uv", "run", "pip-audit"),),
        responsibilities=("dependency-audit",),
    )


def _duplication(profile: Profile) -> Contribution | None:
    if profile.providers.duplication == "none":
        return None
    paths = ("apps", "packages") if profile.preset == "workspace" else ("src",)
    command = ("uv", "run", "pylint", *paths)
    return Contribution(
        provider="duplication-pylint",
        dev_dependencies=(package_requirement("pylint"),),
        files={
            "pylintrc": (
                "[MAIN]\nignore=tests,.venv\n\n"
                "[MESSAGES CONTROL]\ndisable=all\nenable=duplicate-code\n\n"
                "[SIMILARITIES]\nmin-similarity-lines=8\n"
            )
        },
        commands={"duplication": command},
        gates=(command,),
        responsibilities=("duplication",),
    )


def _hooks(profile: Profile) -> Contribution | None:
    provider = profile.providers.hooks
    if provider == "none":
        return None
    if provider == "pre-commit":
        return Contribution(
            provider="hooks-pre-commit",
            dev_dependencies=(package_requirement("pre-commit"),),
            files={".pre-commit-config.yaml": _pre_commit(profile)},
            responsibilities=("git-hooks",),
        )
    return Contribution(
        provider="hooks-lefthook",
        files={"lefthook.yml": _lefthook(profile)},
        responsibilities=("git-hooks",),
    )


def _http(profile: Profile) -> Contribution | None:
    provider = profile.providers.http
    if provider == "none":
        return None
    module = _module_name(profile.project.name)
    if provider == "fastapi":
        logging_import, logging_setup, logging_call = _logging_source(profile)
        content = (
            f"{logging_import}from fastapi import FastAPI\n"
            "from pydantic import BaseModel\n"
            "\n"
            'app = FastAPI(title="Service")\n'
            f"{logging_setup}\n\n"
            "class Health(BaseModel):\n"
            "    status: str\n\n\n"
            '@app.get("/health", response_model=Health)\n'
            "def health() -> Health:\n"
            f"{logging_call}"
            '    return Health(status="ok")\n'
        )
        dependencies = (package_requirement("fastapi"), package_requirement("uvicorn"))
        dev_dependencies = (package_requirement("httpx2"),)
    else:
        content = (
            "from flask import Flask\n\n"
            "app = Flask(__name__)\n\n\n"
            '@app.get("/health")\n'
            "def health() -> dict[str, str]:\n"
            '    return {"status": "ok"}\n'
        )
        dependencies = (package_requirement("flask"),)
        dev_dependencies = ()
    generated = {f"src/{module}/app.py": content}
    if profile.providers.tests != "none":
        generated.update(_test_package_files("tests/integration"))
        generated["tests/integration/test_health.py"] = _http_test(
            module, provider, profile.providers.tests
        )
    return Contribution(
        provider=f"http-{provider}",
        dependencies=dependencies,
        dev_dependencies=dev_dependencies,
        files=generated,
        commands={"serve": _serve_command(profile, module)},
        responsibilities=("http",),
    )


def _logging(profile: Profile) -> Contribution | None:
    if profile.providers.logging == "standard-library":
        return Contribution(provider="logging-standard-library", responsibilities=("logging",))
    if profile.providers.logging == "none":
        return None
    return Contribution(
        provider="logging-structlog",
        dependencies=(package_requirement("structlog"),),
        responsibilities=("logging",),
    )


def _publishing(profile: Profile) -> Contribution | None:
    if profile.providers.publishing == "none":
        return None
    return Contribution(
        provider="publishing-pypi",
        files={".github/workflows/publish.yml": _publish_workflow()},
        commands={"publish": ("uv", "publish")},
        responsibilities=("publishing",),
    )


def _runtime_validation(profile: Profile) -> Contribution | None:
    if profile.providers.runtime_validation == "none":
        return None
    return Contribution(
        provider="validation-pydantic",
        dependencies=(package_requirement("pydantic"),),
        responsibilities=("runtime-validation",),
    )


def _secret_scan(profile: Profile) -> Contribution | None:
    if profile.providers.secret_scan == "none":
        return None
    return Contribution(
        provider="secrets-gitleaks",
        files={
            ".gitleaks.toml": 'title = "Repository secret scanning"\n\n[extend]\nuseDefault = true\n'
        },
        commands={"secrets": ("gitleaks", "detect", "--source", ".")},
        gates=(("gitleaks", "detect", "--source", "."),),
        responsibilities=("secret-scan",),
    )


def _workspace(profile: Profile) -> Contribution | None:
    if profile.providers.workspace == "none":
        return None
    generated: dict[str, str] = {}
    for member in profile.project.workspace_members:
        member_name = _module_name(member.rsplit("/", maxsplit=1)[-1])
        generated[f"{member}/pyproject.toml"] = _workspace_member_pyproject(member_name)
        generated[f"{member}/src/{member_name}/__init__.py"] = '"""Workspace member."""\n'
        if profile.providers.tests != "none":
            generated[f"{member}/tests/__init__.py"] = ""
            generated[f"{member}/tests/test_smoke.py"] = _workspace_test(profile.providers.tests)
    return Contribution(
        provider="workspace-uv",
        files=generated,
        responsibilities=("workspace",),
    )


def _additions(profile: Profile) -> Contribution | None:
    additions = profile.additions
    if not (
        additions.dependencies
        or additions.dev_dependencies
        or additions.commands
        or additions.ci_commands
    ):
        return None
    return Contribution(
        provider="profile-additions",
        dependencies=tuple(additions.dependencies),
        dev_dependencies=tuple(additions.dev_dependencies),
        commands={name: tuple(command) for name, command in additions.commands.items()},
        gates=tuple(tuple(command) for command in additions.ci_commands),
    )


def _module_name(name: str) -> str:
    return name.replace("-", "_").replace(".", "_")


def _test_package_files(directory: str) -> dict[str, str]:
    return {"tests/__init__.py": "", f"{directory}/__init__.py": ""}


def _library_test(module: str, provider: str) -> str:
    if provider == "unittest":
        return (
            "import unittest\n\n"
            f"from {module} import greet\n\n\n"
            "class GreetTest(unittest.TestCase):\n"
            "    def test_greet_returns_a_named_greeting(self) -> None:\n"
            '        self.assertEqual(greet("Ada"), "Hello, Ada!")\n'
        )
    return (
        f"from {module} import greet\n\n\n"
        "def test_greet_returns_a_named_greeting() -> None:\n"
        '    assert greet("Ada") == "Hello, Ada!"\n'
    )


def _cli_test(module: str, cli_provider: str, test_provider: str) -> str:
    if cli_provider == "typer" and test_provider == "unittest":
        return (
            "import unittest\n"
            "from contextlib import redirect_stdout\n"
            "from io import StringIO\n\n"
            f"from {module}.cli import hello\n\n\n"
            "class HelloTest(unittest.TestCase):\n"
            "    def test_hello_prints_a_named_greeting(self) -> None:\n"
            "        output = StringIO()\n\n"
            "        with redirect_stdout(output):\n"
            '            hello("Ada")\n\n'
            '        self.assertEqual(output.getvalue(), "Hello, Ada!\\n")\n'
        )
    if cli_provider == "typer":
        return (
            "from pytest import CaptureFixture\n\n"
            f"from {module}.cli import hello\n\n\n"
            "def test_hello_prints_a_named_greeting(capsys: CaptureFixture[str]) -> None:\n"
            '    hello("Ada")\n'
            "    captured = capsys.readouterr()\n"
            '    assert captured.out == "Hello, Ada!\\n"\n'
        )
    if test_provider == "unittest":
        return (
            "import unittest\n\n"
            "from click.testing import CliRunner\n\n"
            f"from {module}.cli import app\n\n\n"
            "class AppTest(unittest.TestCase):\n"
            "    def test_app_prints_a_named_greeting(self) -> None:\n"
            '        result = CliRunner().invoke(app, ["--name", "Ada"])\n\n'
            "        self.assertEqual(result.exit_code, 0)\n"
            '        self.assertEqual(result.output, "Hello, Ada!\\n")\n'
        )
    return (
        "from click.testing import CliRunner\n\n"
        f"from {module}.cli import app\n\n\n"
        "def test_app_prints_a_named_greeting() -> None:\n"
        '    result = CliRunner().invoke(app, ["--name", "Ada"])\n\n'
        "    assert result.exit_code == 0\n"
        '    assert result.output == "Hello, Ada!\\n"\n'
    )


def _http_test(module: str, http_provider: str, test_provider: str) -> str:
    if http_provider == "fastapi":
        imports = (
            "from fastapi.testclient import TestClient\n\n"
            f"from {module}.app import app\n\n"
            "client = TestClient(app)\n"
        )
        request = 'client.get("/health")'
        payload = "response.json()"
    else:
        imports = f"from {module}.app import app\n"
        request = 'app.test_client().get("/health")'
        payload = "response.get_json()"
    if test_provider == "unittest":
        return (
            "import unittest\n\n"
            f"{imports}\n\n"
            "class HealthTest(unittest.TestCase):\n"
            "    def test_health_returns_ok(self) -> None:\n"
            f"        response = {request}\n\n"
            "        self.assertEqual(response.status_code, 200)\n"
            f'        self.assertEqual({payload}, {{"status": "ok"}})\n'
        )
    return (
        f"{imports}\n\n"
        "def test_health_returns_ok() -> None:\n"
        f"    response = {request}\n\n"
        "    assert response.status_code == 200\n"
        f'    assert {payload} == {{"status": "ok"}}\n'
    )


def _workspace_test(provider: str) -> str:
    if provider == "unittest":
        return (
            "import unittest\n\n\n"
            "class MemberTest(unittest.TestCase):\n"
            "    def test_member_is_ready(self) -> None:\n"
            "        self.assertTrue(True)\n"
        )
    return "def test_member_is_ready() -> None:\n    assert True\n"


def _serve_command(profile: Profile, module: str) -> tuple[str, ...]:
    if profile.providers.http == "fastapi":
        return ("uv", "run", "uvicorn", f"{module}.app:app", "--reload")
    return ("uv", "run", "flask", "--app", f"{module}.app", "run", "--debug")


def _logging_source(profile: Profile) -> tuple[str, str, str]:
    if profile.providers.logging == "structlog":
        return (
            "import structlog\n",
            "logger = structlog.get_logger()\n",
            '    logger.info("health_checked")\n',
        )
    if profile.providers.logging == "standard-library":
        return (
            "import logging\n\n",
            "logger = logging.getLogger(__name__)\n",
            '    logger.info("health checked")\n',
        )
    return "", "", ""


def _gitignore() -> str:
    return """.coverage
.mypy_cache/
.pytest_cache/
.ruff_cache/
.venv/
.vscode/
__pycache__/
build/
dist/
htmlcov/
*.egg-info/
*.py[cod]
"""


def _agents() -> str:
    return """# Agent instructions

Read `docs/coding-standards.md` before changing code.

Use maintained packages for solved, non-domain work. Add custom infrastructure only when no maintained package meets the required contract.

Comments should explain why the code exists when that reason is not clear from names and structure. Do not narrate the code, record change history, preserve abandoned approaches, or write comments longer than the behavior they clarify. Put decisions that need a durable record in an issue or ADR.
"""


def _standards() -> str:
    return """# Coding standards

Use type hints at public boundaries and keep modules focused on one responsibility. Validate untrusted input at the boundary, return useful errors, and keep domain logic independent of frameworks.

Choose a maintained package before writing custom infrastructure. Compare support, security history, API fit, and maintenance cost. Custom code needs a concrete contract that available packages cannot meet and tests for that contract.

Keep formatting, linting, type checking, tests, coverage, duplication detection, dependency auditing, and secret scanning separate. Do not configure two tools to enforce the same rule.

Write comments only for intent, constraints, or non-obvious trade-offs. Names and structure should explain what the code does. Never use comments as change history or as a substitute for deleting dead code.
"""


def _readme(profile: Profile, plan: Plan) -> str:
    checks = _command_block(plan)
    return f"""# {profile.project.name}

{profile.project.description}

## Requirements

- Python {profile.project.python_version}
- [uv](https://docs.astral.sh/uv/)

## Setup

```sh
uv sync --all-groups
```

## Checks

```sh
{checks}
```

See `CONTRIBUTING.md` before opening a change and `docs/coding-standards.md` for the repository standards.
"""


def _contributing(plan: Plan) -> str:
    checks = _command_block(plan)
    return f"""# Contributing

Create a focused branch, add tests for changed behavior, and run the configured checks before opening a pull request.

```sh
uv sync --all-groups
{checks}
```

Use Conventional Commits for commit messages. Keep pull requests small enough to review and explain any user-visible behavior change.
"""


def _security(profile: Profile) -> str:
    repository = profile.project.repository_url or "the repository's private security channel"
    return f"""# Security

Do not open a public issue for a suspected vulnerability. Report it through {repository} with reproduction steps, affected versions, and impact. Do not include live credentials or personal data.
"""


def _ruff_config(profile: Profile) -> str:
    version = profile.project.python_version.replace(".", "")
    return f"""target-version = "py{version}"
line-length = 100

[lint]
select = ["ASYNC", "B", "C4", "E", "F", "I", "PERF", "PIE", "RUF", "SIM", "UP"]

[lint.per-file-ignores]
"tests/**" = ["S101"]
"""


def _coverage_config(profile: Profile) -> str:
    source = "apps\n    packages" if profile.preset == "workspace" else "src"
    return f"""[run]
branch = True
source =
    {source}

[report]
fail_under = {profile.tools.coverage_floor}
show_missing = True
skip_covered = True
"""


def _pytest_config(profile: Profile) -> str:
    testpaths = (
        "\n".join(f"    {member}/tests" for member in profile.project.workspace_members)
        if profile.preset == "workspace"
        else "    tests"
    )
    import_mode = " --import-mode=importlib" if profile.preset == "workspace" else ""
    return f"""[pytest]
addopts = --strict-config --strict-markers --cov --cov-report=term-missing{import_mode}
testpaths =
{testpaths}
markers =
    integration: integration tests
    end_to_end: end-to-end tests
"""


def _github_actions(profile: Profile, plan: Plan) -> str:
    checks = "\n".join(f"      - run: {' '.join(command)}" for command in plan.gates)
    return f"""name: CI

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7
      - uses: astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9 # v9.0.0
        with:
          python-version: "{profile.project.python_version}"
      - run: uv sync --frozen --all-groups
{checks}
"""


def _gitlab_ci(profile: Profile, plan: Plan) -> str:
    checks = "\n".join(f"    - {' '.join(command)}" for command in plan.gates)
    return f"""image: ghcr.io/astral-sh/uv:python{profile.project.python_version}-bookworm-slim

stages: [verify]

verify:
  stage: verify
  script:
    - uv sync --frozen --all-groups
{checks}
"""


def _command_block(plan: Plan) -> str:
    return "\n".join(" ".join(command) for command in plan.gates)


def _pre_commit(profile: Profile) -> str:
    hooks: list[str] = []
    if profile.providers.quality == "ruff":
        hooks.extend(
            [
                _pre_commit_hook("ruff-check", "Ruff check", "uv run ruff check"),
                _pre_commit_hook("ruff-format", "Ruff format check", "uv run ruff format --check"),
            ]
        )
    for index, command in enumerate(_test_commands(profile), start=1):
        suffix = f"-{index}" if len(_test_commands(profile)) > 1 else ""
        hooks.append(
            _pre_commit_hook(
                f"tests{suffix}",
                "Tests",
                command,
                pass_filenames=False,
                stage="pre-push",
            )
        )
    if profile.providers.commit_lint == "commitizen":
        hooks.append(
            _pre_commit_hook(
                "commitizen",
                "Commit message",
                "uv run cz check --commit-msg-file",
                stage="commit-msg",
            )
        )
    if not hooks:
        return "repos: []\n"
    return "repos:\n  - repo: local\n    hooks:\n" + "".join(hooks)


def _lefthook(profile: Profile) -> str:
    sections: list[str] = []
    if profile.providers.quality == "ruff":
        sections.append(
            "pre-commit:\n"
            "  commands:\n"
            "    ruff-check:\n"
            "      run: uv run ruff check {staged_files}\n"
            "    ruff-format:\n"
            "      run: uv run ruff format --check {staged_files}\n"
        )
    if profile.providers.commit_lint == "commitizen":
        sections.append(
            "commit-msg:\n"
            "  commands:\n"
            "    commitizen:\n"
            "      run: uv run cz check --commit-msg-file {1}\n"
        )
    test_commands = _test_commands(profile)
    if test_commands:
        commands = "".join(
            f"    tests-{index}:\n      run: {command}\n"
            for index, command in enumerate(test_commands, start=1)
        )
        sections.append(f"pre-push:\n  commands:\n{commands}")
    return "\n".join(sections)


def _pre_commit_hook(
    identifier: str,
    name: str,
    entry: str,
    *,
    pass_filenames: bool = True,
    stage: str | None = None,
) -> str:
    hook = (
        f"      - id: {identifier}\n"
        f"        name: {name}\n"
        f"        entry: {entry}\n"
        "        language: system\n"
    )
    if not pass_filenames:
        hook += "        pass_filenames: false\n"
    if stage is not None:
        hook += f"        stages: [{stage}]\n"
    return hook


def _test_commands(profile: Profile) -> list[str]:
    if profile.providers.tests == "none":
        return []
    if profile.providers.tests == "pytest":
        return ["uv run pytest"]
    if profile.preset == "workspace":
        return [
            f"uv run python -m unittest discover -s {member}/tests"
            for member in profile.project.workspace_members
        ]
    return ["uv run coverage run -m unittest discover -s tests"]


def _publish_workflow() -> str:
    return """name: Publish

on:
  release:
    types: [published]

permissions:
  contents: read
  id-token: write

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7
      - uses: astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9 # v9.0.0
      - run: uv build
      - run: uv publish
"""


def _workspace_member_pyproject(name: str) -> str:
    return f"""[project]
name = "{name}"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = []

[build-system]
requires = ["uv_build>=0.12,<0.13"]
build-backend = "uv_build"
"""
