# TypeScript Scaffold

Create a new TypeScript repository through Claude Code, Codex, or another agent that supports skills. The generated repository has its own README, contribution guide, coding standards, licence, package configuration, checks, CI, and Git repository.

Generated coding standards are self-contained. TypeScript or testing skills can add workflow guidance, but users do not need another skill to get the repository's engineering baseline.

## Requirements

- Node.js 24
- Git when `initialize_git` is enabled
- The exact package-manager version selected by the profile
- External tools selected by the profile, such as Gitleaks

The skill checks required versions and reports missing commands. It does not install global tools without permission.

## Use it

Ask your agent for the repository you want:

```text
Use typescript-scaffold to create a Fastify service at ./catalog-api with Zod, Pino, Vitest, and GitHub Actions.
```

The skill creates a reusable profile the first time you use a preset. Later requests can reuse that profile or override it for one run.

```text
Use my service profile to create ./billing-api, but use Hono with runtime validation and logging set to none for this repository.
```

A profile is optional. State project-specific choices in the request and the skill applies them to a temporary profile for that run.

```text
Use typescript-scaffold to create a Bun and Turbo monorepo at ./platform with Biome, Vitest, Lefthook, Commitlint, jscpd, Gitleaks, an application under apps/app, and a library under packages/core.
```

## Presets

- `library`: pnpm 11.24.0, tsup, Biome, Vitest, Lefthook, Commitlint, Gitleaks, jscpd, GitHub Actions, and npm publishing
- `service`: npm 11.17.0, Fastify, Zod, Pino, ESLint, Prettier, Vitest, Husky, Commitlint, Gitleaks, jscpd, and GitHub Actions
- `cli`: Yarn 4.18.0, tsup, Biome, the Node.js test runner, and GitHub Actions
- `workspace`: Bun 1.3.14, Turbo, Biome, Vitest, Lefthook, Commitlint, Gitleaks, jscpd, and GitHub Actions, with starter members under `apps/app` and `packages/core`

Profiles expose every selection below, subject to the compatibility rules.

## Generated tool baseline

Selected tools receive usable configuration, not empty placeholders.

- TypeScript enables strict checking, unchecked-index protection, exact optional properties, override checks, switch fallthrough checks, side-effect import checks, isolated modules, JSON modules, and consistent filename casing.
- Biome and ESLint reject explicit `any`, ignored TypeScript errors, enums, and non-null assertions. ESM profiles also reject CommonJS. Formatting and linting have separate commands.
- Prettier uses 100-character lines, two-space indentation, double quotes, semicolons, and trailing commas.
- Vitest and Jest include source files that tests never import and enforce an 80% coverage floor for statements, branches, functions, and lines.
- Commitlint extends Conventional Commits, requires blank lines before bodies and footers, and requires lower-case scopes when a scope is present. Repositories choose their own scope vocabulary.
- Git hooks check staged files before commit, run Commitlint for commit messages, and run type checking and tests before push.
- jscpd checks source code with a 3% duplication threshold and ignores tests, declarations, coverage output, and build output.
- Gitleaks extends its maintained default rules. The scaffold does not copy or weaken that rule set.

These are release-owned starting rules. Edit the generated configuration when a repository needs a justified exception or a stricter policy.

## Provider fields

| Field | Choices |
| --- | --- |
| `preset` | `cli`, `library`, `service`, `workspace` |
| `package_manager` | `bun`, `npm`, `pnpm`, `yarn` |
| `package_manager_version` | Exact semantic version of the selected package manager |
| `module` | `commonjs`, `esm` |
| `build` | `framework-owned`, `tsc`, `tsup` |
| `quality` | `biome`, `eslint-prettier`, `none` |
| `tests` | `jest`, `node-test`, `vitest`, `none` |
| `runtime_validation` | `valibot`, `zod`, `none` |
| `http` | `express`, `fastify`, `hono`, `nestjs`, `none` |
| `logging` | `pino`, `winston`, `none` |
| `hooks` | `husky-lint-staged`, `lefthook`, `none` |
| `commit_lint` | `commitlint`, `none` |
| `ci` | `github-actions`, `gitlab-ci`, `none` |
| `publishing` | `npm`, `none` |
| `workspace` | `nx`, `turbo`, `none` |
| `secret_scan` | `gitleaks`, `none` |
| `duplication` | `jscpd`, `none` |
| `framework` | `vite-react`, `none` |
| `license` | `apache-2.0`, `mit`, `none` |

### Compatibility

- HTTP providers require the `service` preset, and a service requires an HTTP provider.
- Runtime validation and logging integrations currently require Fastify.
- NestJS requires the `tsc` build provider. It supports Vitest, Jest, or no test provider.
- The CLI, Fastify, and NestJS templates require ESM.
- Workspace providers require the `workspace` preset, and a workspace requires either Turbo or Nx.
- npm publishing requires the `library` preset.
- Husky with lint-staged requires ESLint and Prettier.
- Lefthook requires at least one lint or test command.
- Commitlint requires a Git-hook provider and is connected to its commit-message hook.
- Workspace quality and test providers run at the root across every member. Turbo or Nx owns build and type-check fan-out.
- Workspace members currently use the `tsc` build provider.

Vite React uses the `library` preset with `framework: vite-react`, `build: framework-owned`, `quality: none`, `publishing: none`, and `module: esm`. Vite owns linting for this profile. Select Vitest or no test provider. The skill runs the official Vite generator, then applies the selected agent-kit files and checks.

```yaml
preset: library
module: esm
build: framework-owned
quality: none
tests: vitest
framework: vite-react
publishing: none
```

## Profiles

Profiles are complete YAML files with `schema_version: 1`. They are stored outside the installed skill so an agent-kit update cannot overwrite user choices. On Linux, the default directory is:

```text
~/.config/agent-kit/scaffolds/typescript/
```

Set `AGENT_KIT_CONFIG_DIR` to choose another root. Existing profiles are never overwritten by the skill or by an agent-kit update.

This also means an existing profile keeps older explicit defaults. Use a new named profile to start from a newer bundled preset, or edit the existing profile when you want its future repositories to change.

Use a preset name for its default persistent profile, or `<preset>:<name>` for a named profile:

```text
service
service:backend
library:public-packages
```

Per-run overrides use a temporary resolved profile and do not change the persistent file.

### Complete profile

`name` identifies the reusable profile. This example shows every current field:

```yaml
schema_version: 1
name: service
preset: service
package_manager: npm
package_manager_version: 11.17.0
module: esm
build: tsc
quality: eslint-prettier
tests: vitest
runtime_validation: zod
http: fastify
logging: pino
hooks: husky-lint-staged
commit_lint: commitlint
ci: github-actions
publishing: none
workspace: none
workspace_members: []
secret_scan: gitleaks
duplication: jscpd
framework: none
license: apache-2.0
install_dependencies: true
run_quality_gates: true
initialize_git: true
default_author: ""
project:
  name: ""
  description: ""
  author: ""
  repository_url: ""
package_versions: {}
extra_dependencies: []
extra_dev_dependencies: []
extra_scripts: {}
ci_commands: []
```

### Project fields

The `project` object holds values for one generated repository:

```yaml
project:
  name: catalog-api
  description: HTTP API for the product catalog.
  author: Example Maintainer
  repository_url: https://github.com/example/catalog-api.git
```

Leave a field empty in a persistent profile when it changes between repositories. The skill fills it in for the current run. The MIT licence requires a resolved author because the generated copyright notice has no template placeholders.

### Workspace members

`workspace_members` creates initial packages for the workspace preset. Each member has a safe relative path, a reusable package-name template, and a kind.

```yaml
workspace_members:
  - path: apps/app
    package_name: "@{project}/app"
    kind: application
  - path: packages/core
    package_name: "@{project}/core"
    kind: library
```

`{project}` resolves to the generated repository name. Member paths and resolved package names must be unique. An empty list creates an empty workspace with `apps/*` and `packages/*` package globs.

### Package versions and additions

`package_versions` overrides packages owned by selected providers. Version resolution follows this order: profile override, provider-specific default, then global shipped default. Use the `create-vite` key to select the official Vite generator version.

The bundled [defaults file](config/defaults.yaml) is part of agent-kit and may change during an update. Put personal pins in a persistent profile instead of editing the bundled file. Agent-kit never rewrites a persistent profile, but an omitted package version follows the defaults from the installed release.

```yaml
package_versions:
  fastify: ^5.12.1
  zod: ^4.4.3
extra_dependencies:
  - name: nanoid
    version: ^5.1.0
extra_dev_dependencies: []
extra_scripts:
  check: npm run lint && npm test
ci_commands:
  - npm run check
```

Standard lint, type-check, test, build, duplication, and secret-scan jobs are derived from the selected providers and package manager. Use `ci_commands` only for additional commands.

Extra packages do not receive generated integration code. Add a first-class provider when a package needs source templates, configuration, documentation, hooks, compatibility checks, or CI behavior.

### Shipped package defaults

| Package | Version |
| --- | --- |
| `@biomejs/biome` | `^2.5.10` |
| `@commitlint/cli` | `^21.2.2` |
| `@commitlint/config-conventional` | `^21.2.2` |
| `@eslint/js` | `^10.0.1` |
| `@hono/node-server` | `^1.19.11` |
| `@nestjs/common` | `^11.1.17` |
| `@nestjs/core` | `^11.1.17` |
| `@nestjs/platform-express` | `^11.1.17` |
| `@swc/core` | `^1.16.1` |
| `@swc/jest` | `^0.2.39` |
| `@testing-library/jest-dom` | `^7.0.1` |
| `@testing-library/react` | `^16.3.2` |
| `@types/express` | `^5.0.6` |
| `@types/jest` | `^30.0.0` |
| `@types/node` | `^24.13.3` |
| `@vitest/coverage-v8` | `^4.1.11` |
| `eslint` | `^10.9.1` |
| `eslint-config-prettier` | `^10.1.8` |
| `express` | `^5.2.1` |
| `fastify` | `^5.12.1` |
| `hono` | `^4.12.8` |
| `husky` | `^9.1.7` |
| `jest` | `^30.2.0` |
| `jscpd` | `^5.0.16` |
| `jsdom` | `^30.0.1` |
| `lefthook` | `^2.1.10` |
| `lint-staged` | `^17.3.0` |
| `nx` | `^23.1.1` |
| `pino` | `^10.3.1` |
| `prettier` | `^3.9.6` |
| `reflect-metadata` | `^0.2.2` |
| `rxjs` | `^7.8.2` |
| `tsup` | `^8.5.1` |
| `tsx` | `^4.21.0` |
| `turbo` | `^2.10.12` |
| `typescript` | `^6.0.3` |
| `typescript-eslint` | `^8.68.0` |
| `valibot` | `^1.2.0` |
| `vitest` | `^4.1.11` |
| `winston` | `^3.19.0` |
| `zod` | `^4.4.3` |

The `tsup` provider defaults TypeScript to `^5.9.3` because its declaration build does not support TypeScript 6 in this scaffold.

### Other shipped defaults

| Setting | Default |
| --- | --- |
| Generated package version | `0.1.0` |
| Node.js | `24` |
| TypeScript target | `ES2023` |
| Vite generator | `create-vite@9.2.0` |
| GitHub runner | `ubuntu-latest` |
| Checkout action | `actions/checkout@v4` |
| Node setup action | `actions/setup-node@v4` |
| Bun setup action | `oven-sh/setup-bun@v2` |
| pnpm setup action | `pnpm/action-setup@v4` |
| Gitleaks action | `gitleaks/gitleaks-action@v2` |
| GitLab Node image | `node:24` |
| GitLab Gitleaks image | `zricethezav/gitleaks:v8.30.1` |

### Execution controls

- `package_manager_version` is an exact pin. Install that version or change the profile before generation.
- `install_dependencies` installs the selected stack and writes its lockfile. When disabled, generated CI uses a non-frozen install and does not configure lockfile-dependent caching.
- `run_quality_gates` runs every planned check whose package script exists and requires `install_dependencies: true`.
- `initialize_git` creates a `main` Git repository after normal checks pass.
- `default_author` supplies an author when `project.author` is empty.

Schema mismatches fail with the field path and validation message.

## Generated standards

Every repository receives `AGENTS.md` and `docs/coding-standards.md`. They cover dependency selection, maintained-package checks, module boundaries, strict TypeScript, runtime validation, configuration, tests, comments, commits, and the checks selected by the profile. Tool names and commands are generated from the resolved stack.

The generated README lists disabled providers as `none`, so a minimal or deliberately omitted capability remains visible.

## Safety

The scaffold creates new repositories only. It rejects existing targets, runs configured checks before exposing a new target, and initializes Git only after generation and normal checks succeed. It removes staging output after a failure, `SIGINT`, or `SIGTERM`; no process can clean up after `SIGKILL`. It does not create remotes, push, or commit.

## Contributor entry point

The skill calls the bundled generator internally:

```sh
node dist/generate.mjs --profile service --target /path/to/example-service
```

Run `npm test`, `npm run typecheck`, and `npm run check:dist` after changing the generator. The built file, bundled defaults, and JSON Schema are committed so users do not install dependencies inside the skill.
