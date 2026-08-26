# agent-kit

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

```sh
mkdir -p ~/.agents/skills
ln -s /path/to/agent-kit/skills/typescript-scaffold ~/.agents/skills/typescript-scaffold
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

See the [TypeScript scaffold guide](skills/typescript-scaffold/README.md) for presets, profiles, supported providers, and safety boundaries.

## Legacy commands

The files under `commands/` remain available for Claude Code installations that use slash commands:

- [nobs](commands/nobs.md)
- [interview](commands/interview.md)

Copy them into `~/.claude/commands/` when needed. New reusable workflows should be skills.

## Contributing

Keep each skill focused. Put agent instructions in `SKILL.md`, detailed reference material in `references/`, executable helpers in `scripts/`, and generated-output templates in `assets/`. Test behavior and scripts before opening a pull request.

## Licence

[MIT](LICENSE)
