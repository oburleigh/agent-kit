# Configurable TypeScript Scaffold V1

## Purpose

The TypeScript scaffold is a public skill for creating a new repository from a reusable user profile. It provides useful defaults without fixing users to one stack. Each generated repository is complete, independent, and ready for development.

The skill is the user interface. A bundled generator performs the file creation, dependency installation, checks, and Git setup. Users should not need to install or learn a separate scaffold CLI.

## V1 scope

V1 creates TypeScript libraries, services, command-line applications, workspaces, and one delegated frontend example. It supports reusable profiles, per-run overrides, first-class package integrations, generated documentation, continuous integration, and repository setup.

Every generated repository includes:

- `README.md` with sections appropriate to the selected preset
- `CONTRIBUTING.md` with setup, development, test, and contribution guidance
- `.gitignore` for the selected tools
- an Apache 2.0 `LICENSE` by default, with the licence choice configurable
- package scripts and configuration for each selected provider
- a dependency lockfile when installation is enabled
- a Git repository when Git initialization is enabled

V1 does not update repositories after creation, regenerate an existing project, or place the source profile or a scaffold answers file in the generated repository.

## User experience

A typical request is:

> Use typescript-scaffold to create a Fastify service in `./catalog-api` using my `service` profile. Use Zod and Pino, but switch the test runner to Vitest.

The skill:

1. Finds the named profile in the user's agent-kit configuration directory.
2. Offers to create it from a bundled preset if it does not exist.
3. Applies explicit request overrides to an ephemeral, fully resolved execution profile.
4. Shows the resolved stack and target before generation when the request is ambiguous or changes the persistent profile defaults.
5. Runs the bundled generator with only the resolved profile path and target path.
6. Reports the generated stack and the checks that passed.

The internal entry point is:

```text
node dist/generate.mjs --profile <resolved-profile.yaml> --target <directory>
```

This command is documented for contributors and troubleshooting. Normal usage remains skill-driven.

## Profiles and presets

Profiles live outside the installed plugin or skill directory so an update cannot overwrite them. On Linux, the default location is:

```text
~/.config/agent-kit/scaffolds/typescript/
```

The implementation uses the platform's standard user configuration directory on macOS and Windows. A user can override the root with `AGENT_KIT_CONFIG_DIR`.

Bundled presets provide starting points:

- `library`
- `service`
- `cli`
- `workspace`

Creating a profile copies and fully materializes the current preset. Existing profiles are never overwritten. Preset updates affect only profiles created after the update. A profile migration is a separate operation that previews its changes and writes only after explicit approval.

Profiles use YAML and include a `schema_version`. A materialized service profile has this shape:

```yaml
schema_version: 1
name: service
preset: service
package_manager: npm
package_manager_version: "11"
module: esm
build: tsc
quality: eslint-prettier
tests: vitest
runtime_validation: zod
http: fastify
logging: pino
hooks: husky-lint-staged
ci: github-actions
publishing: none
workspace: none
secret_scan: gitleaks
duplication: jscpd
framework: none
license: apache-2.0
install_dependencies: true
run_quality_gates: true
initialize_git: true
default_author: ""
package_versions:
  typescript: "^5.9.0"
  fastify: "^5.0.0"
  pino: "^9.0.0"
  zod: "^4.0.0"
  vitest: "^3.0.0"
extra_dependencies: []
extra_dev_dependencies: []
extra_scripts: {}
ci_commands:
  - npm run lint
  - npm test
  - npm run build
```

The actual preset records all packages selected by its providers. Version values are data, not hardcoded branches in the generator. Users can change them in their persistent profiles. A generated `package.json` and lockfile record the versions used for that repository.

Per-run overrides do not modify a persistent profile unless the user explicitly asks to save them.

## Provider model

A provider is a complete integration for one selectable tool. It owns:

- runtime and development dependencies
- package scripts
- templates and configuration files
- README and contribution-guide fragments
- Git hooks and CI steps where applicable
- compatibility rules
- focused tests

The central planner composes provider outputs into one generation plan. It does not contain package-specific condition chains. Conflicting file writes, script names, dependencies, or compatibility claims fail during planning with an actionable error.

V1 supports these first-class choices:

| Category | Providers |
| --- | --- |
| Package manager | pnpm, npm, Yarn, Bun |
| Preset | library, service, CLI, workspace |
| Module | ESM, CommonJS |
| Build | tsc, tsup, framework-owned |
| Quality | Biome, ESLint with Prettier, none |
| Tests | Vitest, Node test runner, Jest, none |
| Runtime validation | Zod, Valibot, none |
| HTTP | Fastify, Express, Hono, NestJS, none |
| Logging | Pino, Winston, none |
| Hooks | Lefthook, Husky with lint-staged, none |
| CI | GitHub Actions, GitLab CI, none |
| Publishing | npm, none |
| Workspace | none, Turbo, Nx |
| Secret scan | Gitleaks, none |
| Duplication | jscpd, none |

Zod is always used inside the generator for profile validation and inferred types. Adding Zod to the generated repository is controlled by the runtime-validation provider.

Profiles may also declare extra runtime dependencies, development dependencies, package scripts, and CI commands. These additions are copied as configuration. The scaffold does not invent source code, documentation, or integration behavior for an unknown package.

## Framework delegation

Frameworks with maintained official generators keep their native project structure and commands. An adapter runs the official generator in the same outer creation transaction, then applies the agent-kit documentation, repository standards, and compatible providers as an overlay.

V1 includes a Vite React adapter as the first delegated framework path. The adapter pins or records the invoked generator version, supplies non-interactive arguments, validates the resulting tree, and rejects provider combinations that would replace framework-owned behavior.

## Generator architecture

The skill is laid out as:

```text
skills/typescript-scaffold/
├── SKILL.md
├── config/
│   ├── schema.ts
│   ├── schema.json
│   └── presets/
│       ├── library.yaml
│       ├── service.yaml
│       ├── cli.yaml
│       └── workspace.yaml
├── src/
│   ├── generate.ts
│   ├── profiles.ts
│   ├── planning.ts
│   ├── providers.ts
│   └── framework-generators.ts
├── providers/
├── templates/common/
├── dist/generate.mjs
└── tests/
```

The generator uses established packages for established problems:

- Zod validates profiles, provides TypeScript types, and emits `schema.json` from the same schema.
- `yaml` reads and writes YAML without a custom parser.
- `node-plop` renders Handlebars templates and runs conditional file actions.
- `env-paths` resolves the user configuration directory.
- `execa` runs package managers, official framework generators, quality gates, and Git without a custom process wrapper.

The committed `dist/generate.mjs` bundles runtime dependencies. Users need Node.js and the package manager selected by the profile. They do not run an install step inside the plugin cache. Continuous integration rebuilds the bundle and fails when the committed artifact differs.

## Creation transaction

Generation follows this sequence:

```text
request
  -> load and resolve profile
  -> validate with Zod
  -> compose provider plan
  -> verify target
  -> run official generator when selected
  -> render agent-kit files
  -> install dependencies without uncontrolled lifecycle scripts
  -> run configured quality gates
  -> initialize Git
  -> activate and verify Git hooks when selected
  -> expose the completed target
```

An absent target is built in a temporary sibling directory and renamed into place after every step succeeds. An existing non-empty target is always rejected. An existing empty target may be used, but it is preserved if generation fails. Cleanup removes only directories created by the generator.

Git initialization runs only after rendering, installation, and the normal quality gates pass. Git-dependent hook setup and its verification run next. A failure removes generator-owned Git metadata before cleanup, so an incomplete repository is never exposed as a successful result. The scaffold creates the repository but does not create a remote or push commits.

## Failure behavior

The generator fails closed for:

- invalid YAML or a profile that does not match the current schema
- an unsupported provider or schema version
- incompatible providers
- conflicting planned files or scripts
- an unavailable selected package manager
- a non-empty target
- dependency installation failure
- a failed quality gate
- an interrupted official framework generator

Errors identify the profile field or execution step and leave user-owned files untouched.

## Verification

Implementation starts with failing tests for profile validation and non-empty target refusal.

Unit tests cover schema validation and materialization, preset resolution, provider compatibility, dependency and script planning, package version recording, overwrite refusal, and deterministic generation plans.

Render tests generate into temporary directories and verify:

- the exact expected file tree
- dependencies and scripts
- parseable JSON, YAML, and TypeScript configuration
- no files, dependencies, documentation, hooks, or CI from disabled providers
- the generated `README.md`, `CONTRIBUTING.md`, `.gitignore`, and Apache 2.0 licence
- Git initialization only after successful installation and checks

The representative V1 profiles are:

1. A pnpm library with Biome, Vitest, Lefthook, npm publishing, and GitHub Actions.
2. An npm Fastify service with ESLint, Prettier, Jest, Zod, Pino, Husky, and GitLab CI.
3. A Yarn CLI using the Node test runner, with no runtime validation or CI.
4. A Bun workspace using Turbo.
5. A Vite React project created by the official generator and completed with the agent-kit overlay.

Each first-class provider appears in at least one focused render test. Official generator adapters use separate smoke tests because they may require network access. Unit and render suites remain offline and deterministic.

Failure tests cover malformed profiles, unsupported and conflicting providers, missing package managers, failed installs, failed gates, non-empty targets, interrupted generation, existing profiles, and cleanup boundaries. A provider is not listed as supported until its focused test passes.

## Public documentation

`SKILL.md` explains when to use the scaffold, how the skill finds or creates profiles, how per-run overrides work, and the create-only safety boundary. The repository README documents installation for Claude Code and Codex, profile locations, preset creation, and short examples. Internal implementation detail stays in contributor documentation unless it helps users diagnose a failed generation.
