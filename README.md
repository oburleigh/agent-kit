<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/agent-kit-logo-dark.png">
    <source media="(prefers-color-scheme: light)" srcset="assets/agent-kit-logo-light.png">
    <img src="assets/agent-kit-logo-light.png" alt="Agent Kit logo" width="768" height="512">
  </picture>
</p>

Agent Kit is a public marketplace of focused skills for Codex and Claude Code. Add the marketplace once, then install only the plugins you want. Adding the marketplace does not install any plugin.

## Plugins

| Plugin | Use it for |
| --- | --- |
| [create-skill](plugins/create-skill/skills/create-skill/) | Create and validate a reusable Agent Skill. |
| [git-commit](plugins/git-commit/skills/git-commit/) | Review, stage, split, and commit Git changes with Conventional Commits. |
| [humanize](plugins/humanize/skills/humanize/) | Remove common machine-written patterns from professional prose. |
| [typescript-scaffold](plugins/typescript-scaffold/skills/typescript-scaffold/) | Create a configurable TypeScript library, service, CLI, workspace, or Vite React repository. |

## Install for Codex

Add the marketplace:

```sh
codex plugin marketplace add oburleigh/agent-kit
```

Install one plugin:

```sh
codex plugin add typescript-scaffold@agent-kit
```

Or install every current plugin:

```sh
codex plugin add create-skill@agent-kit
codex plugin add git-commit@agent-kit
codex plugin add humanize@agent-kit
codex plugin add typescript-scaffold@agent-kit
```

Start a new Codex session after installation. To fetch marketplace changes and update an installed plugin:

```sh
codex plugin marketplace upgrade agent-kit
codex plugin remove typescript-scaffold@agent-kit
codex plugin add typescript-scaffold@agent-kit
```

Remove a plugin or the marketplace:

```sh
codex plugin remove typescript-scaffold@agent-kit
codex plugin marketplace remove agent-kit
```

## Install for Claude Code

Add the marketplace:

```sh
claude plugin marketplace add oburleigh/agent-kit
```

Install one plugin:

```sh
claude plugin install typescript-scaffold@agent-kit
```

Or install every current plugin:

```sh
claude plugin install create-skill@agent-kit
claude plugin install git-commit@agent-kit
claude plugin install humanize@agent-kit
claude plugin install typescript-scaffold@agent-kit
```

Restart Claude Code after installation. Update the marketplace and an installed plugin with:

```sh
claude plugin marketplace update agent-kit
claude plugin update typescript-scaffold@agent-kit
```

Remove a plugin or the marketplace:

```sh
claude plugin uninstall typescript-scaffold@agent-kit
claude plugin marketplace remove agent-kit
```

Use `--scope project` with the Claude marketplace and install commands when a repository should declare the plugin for its contributors.

## TypeScript scaffold

Ask your agent for a preset and override only what the repository needs:

```text
Use typescript-scaffold to create a Fastify service at ./catalog-api using the service preset. Keep Zod and Pino, but use GitLab CI.
```

For a monorepo:

```text
Use typescript-scaffold to create a Bun and Turbo monorepo at ./platform with Biome, Vitest, Lefthook, Commitlint, Gitleaks, jscpd, an application under apps/app, and a library under packages/core.
```

The scaffold requires Node.js 24. Its presets provide working defaults, while user profiles keep personal choices outside the plugin cache so updates do not overwrite them. See the [TypeScript scaffold guide](plugins/typescript-scaffold/skills/typescript-scaffold/README.md) for presets, profiles, providers, generated files, and safety boundaries.

## Local development

Clone the repository and add its path as a marketplace source:

```sh
git clone https://github.com/oburleigh/agent-kit.git
codex plugin marketplace add ./agent-kit
claude plugin marketplace add ./agent-kit
```

Each plugin keeps its Agent Skill under `plugins/<name>/skills/`. The files under `commands/` are not part of any published plugin.

## Contributing

Keep each skill focused. Put agent instructions in `SKILL.md`, detailed reference material in `references/`, executable helpers in `scripts/`, and generated-output templates in `assets/`. Run the skill's tests and both runtime validators before opening a pull request.

## Licence

[MIT](LICENSE)
