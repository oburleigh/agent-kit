# TypeScript scaffold profiles

Profiles are fully resolved YAML files with `schema_version: 1`. Change a persistent profile to affect future repositories. Use a temporary copy for a single repository.

## Provider fields

| Field | Choices |
| --- | --- |
| `preset` | `library`, `service`, `cli`, `workspace` |
| `package_manager` | `pnpm`, `npm`, `yarn`, `bun` |
| `package_manager_version` | Exact semantic version of the selected package manager |
| `module` | `esm`, `commonjs` |
| `build` | `tsc`, `tsup`, `framework-owned` |
| `quality` | `biome`, `eslint-prettier`, `none` |
| `tests` | `vitest`, `node-test`, `jest`, `none` |
| `runtime_validation` | `zod`, `valibot`, `none` |
| `http` | `fastify`, `express`, `hono`, `nestjs`, `none` |
| `logging` | `pino`, `winston`, `none` |
| `hooks` | `lefthook`, `husky-lint-staged`, `none` |
| `ci` | `github-actions`, `gitlab-ci`, `none` |
| `publishing` | `npm`, `none` |
| `workspace` | `none`, `turbo`, `nx` |
| `secret_scan` | `gitleaks`, `none` |
| `duplication` | `jscpd`, `none` |
| `framework` | `none`, `vite-react` |
| `license` | `apache-2.0`, `mit`, `none` |

The Vite React adapter requires the library preset, `framework-owned` build, ESM, quality set to `none`, publishing set to `none`, and either Vitest or no test provider. Vite owns linting for this profile. HTTP providers require the service preset. Runtime validation and logging integrations currently require Fastify. NestJS tests require Vitest or Jest. The CLI, Fastify, and NestJS templates require ESM. Workspace providers require the workspace preset. npm publishing requires the library preset. Husky with lint-staged requires ESLint and Prettier. Lefthook requires at least one lint or test command.

Use this combination for a Vite React application:

```yaml
preset: library
module: esm
build: framework-owned
quality: none
tests: vitest
framework: vite-react
publishing: none
```

## Project fields

The `project` object holds values for one generated repository:

```yaml
project:
  name: catalog-api
  description: HTTP API for the product catalog.
  author: Example Maintainer
  repository_url: https://github.com/example/catalog-api.git
```

Leave a field empty in a persistent profile when it changes between repositories. The skill fills it in a temporary execution profile.

## Package versions and additions

`package_versions` pins or ranges the packages owned by selected providers. A provider default is used when its package is absent. Use the `create-vite` key to select the official Vite generator version. Add ordinary packages through:

```yaml
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

## Execution controls

- `package_manager_version` is an exact pin. Install that version or change the profile before generation.
- `install_dependencies` installs the selected stack and writes its lockfile. When disabled, generated CI uses a non-frozen install and does not configure lockfile-dependent caching.
- `run_quality_gates` runs every planned check whose package script exists and requires `install_dependencies: true`.
- `initialize_git` creates a `main` Git repository after normal checks pass.
- `default_author` supplies an author when `project.author` is empty.

Schema mismatches fail with the field path and validation message. Agent-kit updates do not rewrite persistent profiles.
