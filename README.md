<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/agent-kit-logo-dark.png">
    <source media="(prefers-color-scheme: light)" srcset="assets/agent-kit-logo-light.png">
    <img src="assets/agent-kit-logo-light.png" alt="Agent Kit logo" width="768" height="512">
  </picture>
</p>

Reusable skills and agent instructions for software work. Each skill is self-contained under `skills/` and follows the Agent Skills format.

## Skills

| Skill | Use it for |
| --- | --- |
| [typescript-scaffold](skills/typescript-scaffold/) | Create a configurable TypeScript library, service, CLI, workspace, or Vite React repository. |
| [create-skill](skills/create-skill/) | Create and check an Agent Skill. |
| [git-commit](skills/git-commit/) | Review, stage, split, and commit Git changes with Conventional Commits. |
| [humanize](skills/humanize/) | Remove common machine-written patterns from professional prose. |

## Install from one local checkout

Clone the repository once:

```sh
git clone https://github.com/oburleigh/agent-kit.git
cd agent-kit
```

Symlink a skill into each agent that should use it. Replace `/path/to/agent-kit` with the absolute clone path.

### Claude Code

```sh
mkdir -p ~/.claude/skills
ln -s /path/to/agent-kit/skills/typescript-scaffold ~/.claude/skills/typescript-scaffold
```

### Codex and other Agent Skills clients

Use the shared Agent Skills directory when the same checkout should serve more than one client:

```sh
mkdir -p ~/.agents/skills
ln -s /path/to/agent-kit/skills/typescript-scaffold ~/.agents/skills/typescript-scaffold
```

For a Codex-only installation, use the Codex skills directory instead:

```sh
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
ln -s /path/to/agent-kit/skills/typescript-scaffold "${CODEX_HOME:-$HOME/.codex}/skills/typescript-scaffold"
```

The two links can point to the same checkout. Edit the repository copy and both agents see the change. Pull repository updates with:

```sh
git pull --ff-only
```

The TypeScript scaffold stores user profiles outside the checkout, so updates do not replace them.

To install a skill without a symlink, copy its complete directory into the matching skills directory.

## TypeScript scaffold example

Ask your agent:

```text
Use typescript-scaffold to create a Fastify service at ./catalog-api using the service profile. Keep Zod and Pino, but use GitLab CI for this repository.
```

For a monorepo:

```text
Use typescript-scaffold to create a Bun and Turbo monorepo at ./platform with Biome, Vitest, Lefthook, Commitlint, Gitleaks, jscpd, an application under apps/app, and a library under packages/core.
```

See the [TypeScript scaffold guide](skills/typescript-scaffold/README.md) for presets, profiles, supported providers, and safety boundaries.

The TypeScript scaffold requires Node.js 24. Its profile selects an exact package-manager version and may require an external command such as Gitleaks. The skill reports missing prerequisites before changing the requested target. Generated repositories include their own stack-aware coding standards; companion skills are optional.

## Legacy commands

The files under `commands/` remain available for Claude Code installations that use slash commands:

- [nobs](commands/nobs.md)
- [interview](commands/interview.md)

Copy them into `~/.claude/commands/` when needed. New reusable workflows should be skills.

## Contributing

Keep each skill focused. Put agent instructions in `SKILL.md`, detailed reference material in `references/`, executable helpers in `scripts/`, and generated-output templates in `assets/`. Test behavior and scripts before opening a pull request.

## Licence

[MIT](LICENSE)
