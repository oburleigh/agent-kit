# Python Scaffold and Plugin Distribution Design

## Scope

Agent Kit will distribute its skills as independently installable Codex and Claude plugins. The first new plugin is a configurable Python repository scaffold with the same create-only safety and provider model as the TypeScript scaffold.

This work also moves the existing public skills into the shared plugin layout and replaces the README's symlink instructions with marketplace installation. Existing skill behavior stays unchanged unless the move requires a path update.

Legacy files under `commands/` are outside this release. They remain in the repository but are not included in either marketplace. A command should become a skill only after its workflow, boundaries, and tests are strong enough for public use.

## Goals

- Let users install one skill, several skills, or every published skill without symlinks.
- Keep one copy of each skill's instructions and resources for both runtimes.
- Generate new Python libraries, services, CLIs, and uv workspaces from reusable profiles.
- Supply working configuration for every selected tool.
- Generate a complete repository baseline, including Git, documentation, CI, tests, hooks, and coding standards.
- Keep personal profiles outside the installed plugin so updates cannot replace them.
- Reject incompatible stacks before creating the target directory.

Retrofitting existing repositories, managing remote repositories, and maintaining generated repositories are not part of the scaffold.

## Plugin and Marketplace Layout

Each installable plugin owns its manifests and one skill directory:

```text
.agents/plugins/marketplace.json
.claude-plugin/marketplace.json
plugins/
  python-scaffold/
    .codex-plugin/plugin.json
    .claude-plugin/plugin.json
    skills/
      python-scaffold/
        SKILL.md
        README.md
        config/
        scripts/
        src/
        tests/
  typescript-scaffold/
    .codex-plugin/plugin.json
    .claude-plugin/plugin.json
    skills/
      typescript-scaffold/
        ...
```

The existing `create-skill`, `git-commit`, `humanize`, and `typescript-scaffold` directories move into the same structure. Files inside a skill use paths relative to that skill, so the instructions work from either plugin cache.

The Codex marketplace marks every entry `AVAILABLE`, not `INSTALLED_BY_DEFAULT`. Claude also exposes each directory as a separate marketplace entry. Users therefore choose the exact subset they want. The README includes individual installation commands and an install-all command sequence.

There is no separate all-skills plugin in version 1. Such a bundle would need copies, symlinks, or runtime-specific dependency behavior. The install-all sequence gives the same user outcome without duplicated skill names or sources.

Codex and Claude manifests contain only runtime metadata and a path to `./skills/`. Skill content is never forked by runtime. Repository CI validates both manifests and installs plugins from the local marketplaces as a smoke test.

Each plugin has its own semantic version. Its Codex and Claude manifests use the same version, and CI rejects a mismatch. Marketplace entries do not repeat versions. Updating a marketplace can therefore change installed plugins without installing any plugin the user did not select.

## Python Scaffold Interface

The `python-scaffold` skill accepts a target, a profile selector or profile path, and per-run overrides. Natural-language requests are resolved by the agent into a temporary YAML profile before the generator runs.

The generator command is:

```sh
uv run --project <skill-directory> python -m python_scaffold \
  --profile <profile-or-selector> \
  --target <target>
```

The skill supports these selectors:

- `cli`
- `library`
- `service`
- `workspace`
- `<preset>:<profile-name>` for a named profile
- a path to a complete YAML profile

Bundled presets are release-owned. Persistent profiles live under `~/.config/agent-kit/scaffolds/python/` by default. `AGENT_KIT_CONFIG_DIR` can set a different config root. The generator creates a persistent profile only when it does not exist. Per-run changes use a temporary resolved profile and never modify the persistent file unless the user explicitly asks to save them.

## Configuration Model

Pydantic models are the source of truth for profile validation. The project exports a JSON Schema generated from those models and checks the schema into the skill for editor support. Bundled presets and test fixtures must validate against the same models.

Every profile has `schema_version: 1`, a profile name, a preset, provider selections, project metadata, tool settings, optional additions, and execution toggles.

Project-specific values include:

- name
- description
- author
- repository URL
- Python version
- workspace members

Tool settings include the coverage floor and selected test tiers. Extension fields allow extra runtime dependencies, development dependencies, commands, and CI commands. Extra packages do not receive generated integration code. A package that needs source files, configuration, hooks, documentation, or CI behavior requires a first-class provider.

Execution toggles control dependency installation, quality gates, and Git initialization. Disabling a step does not remove its generated configuration.

## Provider Fields

Actual products are listed alphabetically. `none` is always last.

| Field | Choices |
| --- | --- |
| `preset` | `cli`, `library`, `service`, `workspace` |
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

`uv` is the only environment and dependency manager in version 1. It is part of the scaffold runtime rather than a provider choice. This keeps lockfiles, commands, workspaces, and CI consistent while the stack above remains configurable.

Providers contribute dependencies, `pyproject.toml` sections, source templates, tool configuration, hooks, CI steps, documentation, and quality-gate commands through one defined interface. The planner composes those contributions and rejects duplicate paths, dependency conflicts, command-name collisions, and overlapping tool responsibilities.

## Presets

The presets are useful starting points. Users can override any compatible field in a persistent profile or for one run.

### Library

- Python 3.14 and uv-build
- Ruff, ty, and pytest
- pre-commit and Commitizen
- GitHub Actions
- pip-audit, Gitleaks, and duplicate-only Pylint
- PyPI build and package checks

### Service

- Python 3.14 and uv-build
- FastAPI, Pydantic, and structlog
- Ruff, ty, and pytest with unit and integration tiers
- pre-commit and Commitizen
- GitHub Actions
- pip-audit, Gitleaks, Import Linter, and duplicate-only Pylint

### CLI

- Python 3.14 and uv-build
- Typer and standard-library logging
- Ruff, ty, and pytest with unit and end-to-end tiers
- pre-commit and Commitizen
- GitHub Actions
- pip-audit, Gitleaks, and duplicate-only Pylint

### Workspace

- Python 3.14, a uv workspace, and uv-build members
- starter members under `apps/app` and `packages/core`
- Ruff, ty, and pytest across all members
- pre-commit and Commitizen
- GitHub Actions
- pip-audit, Gitleaks, and duplicate-only Pylint

## Compatibility Rules

Validation happens before filesystem mutation.

- A service requires FastAPI or Flask. HTTP providers are limited to services.
- FastAPI requires Pydantic in version 1 because the generated boundary models use it.
- A CLI requires Click or Typer. CLI providers are limited to the CLI preset.
- A workspace requires `uv-workspace` and at least one member.
- PyPI publishing is limited to libraries.
- Import Linter requires a generated layered package layout.
- Selected test tiers must match generated test directories and CI commands.
- Commitizen requires a hook provider so commit-message checks are active.
- Hook configuration can call only commands contributed by selected providers.
- Pylint is configured only for duplicate-code detection. Ruff owns general linting.
- Publishing checks include package build, Twine metadata validation, and wheel-content validation.

## Generated Repository

Every generated repository includes:

- `README.md` with project purpose, setup, commands, structure, configuration, testing, and release sections
- `CONTRIBUTING.md`
- `SECURITY.md`
- `AGENTS.md`
- `docs/coding-standards.md`
- the selected Apache 2.0 or MIT licence, unless licensing is disabled
- `.gitignore`
- `pyproject.toml`, `uv.lock` when dependencies are installed, source, and tests
- selected tool configuration, hooks, and CI
- a new local Git repository when Git initialization is enabled

Generated coding standards are complete on their own. Other Python or testing skills may add workflow help, but the repository does not depend on them for its engineering baseline.

The standards require maintained packages for solved, non-domain work. Custom infrastructure is acceptable only when existing packages cannot meet the required contract. The exception must be narrow, tested, and recorded in maintained documentation when future contributors need the constraint.

Ruff owns formatting and general linting. The selected type checker uses strict settings. Pytest coverage includes source files that tests never import and enforces an 80 percent default floor for lines and branches. Hooks format and lint staged Python files, validate commit messages, and run typing and tests before push. Gitleaks extends its maintained rules rather than copying or weakening them.

## Comment Standard

Generated `AGENTS.md` and `docs/coding-standards.md` use this contract:

> Comments explain non-obvious intent, constraints, invariants, hazards, or external specifications. Do not restate code, narrate implementation steps, preserve change history, or compensate for unclear names. Prefer one short sentence. If a comment is longer than the code it explains, simplify the code or move necessary detail into maintained documentation. Public API docstrings describe the contract, not the implementation.

Comments must stay accurate as code changes. Ticket history, dates, discarded approaches, and explanations of past edits belong in version control or decision records, not source comments. TODO comments are allowed only for a concrete unfinished action and should identify an owner or tracked issue when the repository has one.

This is a concise adaptation of guidance to explain why rather than what, avoid duplicating code, and keep comments current: [Stack Overflow](https://stackoverflow.blog/2021/12/23/best-practices-for-writing-code-comments/) and [Harshith Gowda](https://medium.com/@harshithgowdakt/demystifying-code-comments-when-why-and-how-to-use-them-effectively-540285edc80f).

## Generation Transaction

Generation is create-only. The target must not exist.

1. Resolve and validate the profile.
2. Check required commands and versions.
3. Compose provider contributions into an in-memory plan.
4. Render into a staging directory beside the requested target.
5. Install dependencies and run selected gates in the staging directory.
6. Initialize Git and install hooks in the staging directory.
7. Rename the completed staging directory to the target atomically.

If rendering, installation, a quality gate, or Git setup fails, the generator reports the failing command and removes only its staging directory. It never removes or changes a user-owned target. The atomic rename is the last mutation, so a failed run cannot leave a partial target.

The generator does not create a remote, push, or make an initial commit unless a later version adds an explicit, separately approved option.

## Test Strategy

Tests follow the same boundary structure as the generator.

Unit and integration coverage includes:

- schema generation and profile validation
- persistent profile creation without overwrite
- temporary override resolution
- provider contribution composition
- compatibility and collision failures
- deterministic planning and rendering
- target refusal and staging cleanup
- generated documentation and comment rules
- both marketplace schemas and every plugin manifest

Acceptance tests create real repositories for:

- a library that builds a valid wheel
- a FastAPI service with Pydantic boundary validation
- a Typer CLI exercised in a subprocess
- a uv workspace with application and library members

An alternate-provider matrix covers mypy, Pyright, Flask, Click, Lefthook, GitLab CI, Hatchling, setuptools, and unittest without testing every possible Cartesian combination.

Mutation probes prove that selected gates fail for a Ruff violation, a typing error, insufficient coverage, an invalid commit message, and a failing pre-push check. Local marketplace smoke tests install a subset of plugins into isolated Codex and Claude test locations and confirm that only the selected skills appear.

## Delivery Order

1. Add failing tests for the Python schema, profile resolution, provider planner, renderer, and create-only transaction.
2. Implement the Python generator and bundled presets until the repository acceptance matrix passes.
3. Move existing skills into independent plugin roots and update relative paths and CI commands.
4. Add Codex and Claude manifests and marketplace catalogs.
5. Replace symlink documentation with subset installation and update instructions.
6. Run both runtime validators, local installation smoke tests, Python acceptance tests, and the existing TypeScript scaffold suite.

The old standalone Python skill outside this repository is not changed or removed during development. It can be retired separately after the published plugin passes installation and generation tests.

## Acceptance Criteria

- A user can install only `python-scaffold` in Codex or Claude without a symlink.
- A user can install any combination of published skills without receiving unselected skills.
- Both marketplaces and every plugin manifest pass their runtime validators.
- A profile update in Agent Kit does not overwrite a user's persistent profile.
- All four Python presets generate repositories that pass their selected checks.
- Every selected tool has working configuration and a real command that uses it.
- Incompatible profiles fail before the target exists.
- Failed generation leaves no target and preserves user-owned paths.
- Generated repositories contain usable README, contribution, security, licence, Git, CI, and coding-standard files.
- The generated comment standard rejects verbose narration and historical commentary.
- The TypeScript scaffold still passes its full suite after the plugin move.
