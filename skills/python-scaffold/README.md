# Python Scaffold

Create Python libraries, services, command-line applications, and uv workspaces through Codex, Claude Code, or another Agent Skills runtime.

Generated repositories include source code, tests, a README, contribution and security guides, coding standards, a licence, `.gitignore`, CI, tool configuration, and optional Git initialization. Selected checks have working rules and thresholds rather than empty config files.

## Requirements

- Python 3.14
- [uv](https://docs.astral.sh/uv/)
- Git when `initialize_git` is enabled
- External tools selected by the profile, such as Gitleaks or Lefthook

## Use it

Ask for the repository and stack you need:

```text
Use python-scaffold to create a FastAPI service at ./catalog-api with Pydantic, Structlog, Ruff, pytest, ty, pre-commit, Commitizen, Gitleaks, and GitHub Actions.
```

The first use of a preset creates a persistent profile. Later requests can reuse that profile or apply temporary changes for one repository.

```text
Use my service profile to create ./billing-api, but use Flask, Mypy, unittest, Lefthook, and GitLab CI for this repository.
```

Add `--plan` to the scaffold command to print the resolved project, providers, workspace members, execution settings, and quality gates as JSON. Planning does not create a profile or repository.

## Presets

- `library`: uv-build, Ruff, pytest, ty, pre-commit, Commitizen, pip-audit, duplicate-only Pylint, Gitleaks, GitHub Actions, and PyPI publishing
- `service`: the library baseline plus FastAPI, Pydantic, Structlog, HTTP integration tests, and Import Linter
- `cli`: the core baseline plus Typer and end-to-end test support
- `workspace`: a virtual uv workspace with starter members under `apps/app` and `packages/core`

Presets are defaults. Profiles can select the alternatives below.

## Provider fields

| Field | Choices |
| --- | --- |
| `architecture` | `import-linter`, `none` |
| `build_backend` | `hatchling`, `setuptools`, `uv-build` |
| `ci` | `github-actions`, `gitlab-ci`, `none` |
| `cli` | `click`, `typer`, `none` |
| `commit_lint` | `commitizen`, `none` |
| `dependency_audit` | `pip-audit`, `none` |
| `duplication` | `pylint`, `none` |
| `hooks` | `lefthook`, `pre-commit`, `none` |
| `http` | `fastapi`, `flask`, `none` |
| `license` | `apache-2.0`, `mit`, `none` |
| `logging` | `standard-library`, `structlog`, `none` |
| `publishing` | `pypi`, `none` |
| `quality` | `ruff`, `none` |
| `runtime_validation` | `pydantic`, `none` |
| `secret_scan` | `gitleaks`, `none` |
| `tests` | `pytest`, `unittest`, `none` |
| `type_checker` | `mypy`, `pyright`, `ty`, `none` |
| `workspace` | `uv-workspace`, `none` |

### Compatibility

- Services require FastAPI or Flask. Other presets cannot select an HTTP provider.
- FastAPI requires Pydantic.
- CLI repositories require Click or Typer. Other presets cannot select a CLI provider.
- Workspaces require `uv-workspace` and at least one safe relative member path.
- PyPI publishing is limited to libraries.
- Commitizen requires a hook provider.
- Import Linter is limited to libraries and services.
- Test tiers must match the preset and require a test provider.

## Profiles

Profiles are complete YAML files with `schema_version: 1`. Use a preset name for its default profile or `<preset>:<name>` for a named profile:

```text
service
service:backend
library:public-packages
```

On Linux, profiles default to `~/.config/agent-kit/scaffolds/python/`. Set `AGENT_KIT_CONFIG_DIR` to choose another root. Existing profiles are never overwritten.

```yaml
schema_version: 1
profile_name: backend
preset: service
providers:
  architecture: import-linter
  build_backend: uv-build
  ci: github-actions
  cli: none
  commit_lint: commitizen
  dependency_audit: pip-audit
  duplication: pylint
  hooks: pre-commit
  http: fastapi
  license: apache-2.0
  logging: structlog
  publishing: none
  quality: ruff
  runtime_validation: pydantic
  secret_scan: gitleaks
  tests: pytest
  type_checker: ty
  workspace: none
project:
  name: catalog-api
  description: Product catalogue service
  author: Example Maintainer
  repository_url: https://github.com/example/catalog-api
  python_version: "3.14"
  workspace_members: []
tools:
  coverage_floor: 80
  test_tiers: [unit, integration]
additions:
  dependencies: []
  dev_dependencies: []
  commands: {}
  ci_commands: []
execution:
  install_dependencies: true
  run_quality_gates: true
  initialize_git: true
```

Use `additions` for packages and commands that do not need generated integration code. Add a first-class provider when a package needs source templates, configuration, hooks, CI behavior, or compatibility rules.

## Safety

Generation is create-only and atomic. Existing targets are rejected before work starts. Rendering, dependency installation, checks, and Git setup happen in a staging directory; a failed run removes only that staging directory.

Each successful external command prints one `PASS` line. The generator reports the full command-log directory at the end of the run. A failed command includes a short tail from both output streams and keeps the complete logs in the reported directory. Set `AGENT_KIT_LOG_DIR` to choose a different log root.

## Contributor entry point

Run `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, and
`uv run ty check` after changing the generator. Regenerate the committed JSON
Schema with [`scripts/export_schema.py`](scripts/export_schema.py).
