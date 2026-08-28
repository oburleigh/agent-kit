from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from python_scaffold.paths import require_normalized_relative_path

Preset = Literal["cli", "library", "service", "workspace"]
TestTier = Literal["end-to-end", "integration", "unit"]


def default_test_tiers() -> list[TestTier]:
    return ["unit"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")


class Providers(StrictModel):
    architecture: Literal["import-linter", "none"]
    build_backend: Literal["hatchling", "setuptools", "uv-build"]
    ci: Literal["github-actions", "gitlab-ci", "none"]
    cli: Literal["click", "typer", "none"]
    commit_lint: Literal["commitizen", "none"]
    dependency_audit: Literal["pip-audit", "none"]
    duplication: Literal["pylint", "none"]
    hooks: Literal["lefthook", "pre-commit", "none"]
    http: Literal["fastapi", "flask", "none"]
    license: Literal["apache-2.0", "mit", "none"]
    logging: Literal["standard-library", "structlog", "none"]
    publishing: Literal["pypi", "none"]
    quality: Literal["ruff", "none"]
    runtime_validation: Literal["pydantic", "none"]
    secret_scan: Literal["gitleaks", "none"]
    tests: Literal["pytest", "unittest", "none"]
    type_checker: Literal["mypy", "pyright", "ty", "none"]
    workspace: Literal["uv-workspace", "none"]


class Project(StrictModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    author: str = Field(min_length=1)
    repository_url: str | None = None
    python_version: str = Field(pattern=r"^3\.\d+$")
    workspace_members: list[str] = Field(default_factory=list)

    @field_validator("workspace_members")
    @classmethod
    def validate_workspace_members(cls, members: list[str]) -> list[str]:
        return [require_normalized_relative_path(member) for member in members]


class Tools(StrictModel):
    coverage_floor: int = Field(default=80, ge=0, le=100)
    test_tiers: list[TestTier] = Field(default_factory=default_test_tiers)


class Additions(StrictModel):
    dependencies: list[str] = Field(default_factory=list)
    dev_dependencies: list[str] = Field(default_factory=list)
    commands: dict[str, list[str]] = Field(default_factory=dict)
    ci_commands: list[list[str]] = Field(default_factory=list)


class Execution(StrictModel):
    install_dependencies: bool = True
    run_quality_gates: bool = True
    initialize_git: bool = True


class Profile(StrictModel):
    schema_version: Literal[1]
    profile_name: str = Field(min_length=1)
    preset: Preset
    providers: Providers
    project: Project
    tools: Tools = Field(default_factory=Tools)
    additions: Additions = Field(default_factory=Additions)
    execution: Execution = Field(default_factory=Execution)

    @model_validator(mode="after")
    def validate_stack(self) -> Self:
        providers = self.providers

        if self.preset == "service" and providers.http == "none":
            raise ValueError("A service requires FastAPI or Flask")
        if self.preset != "service" and providers.http != "none":
            raise ValueError("HTTP providers are limited to services")
        if providers.http == "fastapi" and providers.runtime_validation != "pydantic":
            raise ValueError("FastAPI requires Pydantic")

        if self.preset == "cli" and providers.cli == "none":
            raise ValueError("A CLI requires Click or Typer")
        if self.preset != "cli" and providers.cli != "none":
            raise ValueError("CLI providers are limited to the CLI preset")

        if self.preset == "workspace":
            if providers.workspace != "uv-workspace" or not self.project.workspace_members:
                raise ValueError("A workspace requires uv-workspace and at least one member")
        elif providers.workspace != "none" or self.project.workspace_members:
            raise ValueError("Workspace configuration is limited to the workspace preset")

        if providers.publishing == "pypi" and self.preset != "library":
            raise ValueError("PyPI publishing is limited to libraries")
        if providers.commit_lint == "commitizen" and providers.hooks == "none":
            raise ValueError("Commitizen requires a hook provider")
        if providers.architecture == "import-linter" and self.preset not in {"library", "service"}:
            raise ValueError("Import Linter requires a layered library or service")

        allowed_tiers: dict[Preset, set[TestTier]] = {
            "cli": {"unit", "end-to-end"},
            "library": {"unit"},
            "service": {"unit", "integration"},
            "workspace": {"unit", "integration"},
        }
        selected_tiers = set(self.tools.test_tiers)
        if providers.tests == "none" and selected_tiers:
            raise ValueError("Test tiers require a test provider")
        if providers.tests != "none" and not selected_tiers:
            raise ValueError("A test provider requires at least one test tier")
        if not selected_tiers <= allowed_tiers[self.preset]:
            raise ValueError(f"Test tiers do not match the {self.preset} preset")

        return self
