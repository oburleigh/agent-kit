# TypeScript Scaffold

Create a new TypeScript repository through Claude Code, Codex, or another agent that supports skills. The generated repository has its own README, contribution guide, coding instructions, licence, package configuration, checks, CI, and Git repository.

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

## Presets

- `library`: pnpm, tsup, Biome, Vitest, Lefthook, GitHub Actions, and npm publishing
- `service`: npm, Fastify, Zod, Pino, ESLint, Prettier, Vitest, Husky, and GitHub Actions
- `cli`: Yarn, tsup, Biome, the Node.js test runner, and GitHub Actions
- `workspace`: Bun, Turbo, TypeScript base configuration, and GitHub Actions, with an empty `packages/` directory ready for independently configured packages

Every selection can be changed in a profile. Supported providers are listed in [references/profiles.md](references/profiles.md).

Vite React uses the `library` preset with `framework: vite-react`, `build: framework-owned`, `quality: none`, `publishing: none`, and `module: esm`. Vite owns linting for this profile. Select Vitest or no test provider. The skill runs the official Vite generator, then applies the selected agent-kit files and checks.

## Profiles

Profiles are stored outside the installed skill. On Linux, the default directory is:

```text
~/.config/agent-kit/scaffolds/typescript/
```

Set `AGENT_KIT_CONFIG_DIR` to choose another root. Existing profiles are never overwritten by the skill or by an agent-kit update.

Use a preset name for its default persistent profile, or `<preset>:<name>` for a named profile:

```text
service
service:backend
library:public-packages
```

Per-run overrides use a temporary resolved profile and do not change the persistent file.

## Safety

The scaffold creates new repositories only. It rejects existing targets, runs configured checks before exposing a new target, and initializes Git only after generation and normal checks succeed. It removes staging output after a failure, `SIGINT`, or `SIGTERM`; no process can clean up after `SIGKILL`. It does not create remotes, push, or commit.

## Contributor entry point

The skill calls the bundled generator internally:

```sh
node dist/generate.mjs --profile config/presets/service.yaml --target /path/to/example-service
```

Run `npm test`, `npm run typecheck`, and `npm run check:dist` after changing the generator. The built file and JSON Schema are committed so users do not install dependencies inside the skill.
