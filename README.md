# agent-kit

Skills, commands, and resources that make AI coding agents better at their job. Works with Claude Code, Cursor, Copilot, Codex, and anything else that accepts structured instructions.

This is a living collection. Each skill is tested in real workflows before it lands here.

---

## Quick nav

**[Skills](#skills)** | **[Commands](#commands)** | **[Installation](#installation)** | **[Learn more](#learn-more)** | **[Contributing](#contributing)**

---

## Skills

Skills are packaged instructions that teach an agent how to handle a specific task well. Not a one-line system prompt. Each one includes the reasoning behind its rules, reference material the agent can look up at runtime, and enough edge-case coverage that the agent doesn't fall apart when things get messy.

| Skill | Description |
|-------|-------------|
| [humanize](skills/humanize/) | Catches and rewrites AI writing patterns in docs, PRs, commit messages, and reports. Maintains a 60+ word blacklist, detects structural tics, and learns from corrections over time. |
| [git-commit](skills/git-commit/) | Produces clean git commits following Conventional Commits v1.0.0. Checks branch protection, stages files selectively, splits unrelated changes into separate commits, and respects project-specific conventions. |

## Commands

Slash commands and shorter task-specific instructions. This section is growing.

| Command | Description |
|---------|-------------|
| [nobs](commands/nobs.md) | Serious-mode prompt wrapper. Forces deep, critical thinking and cuts sycophancy, fabrication, and filler. Usage: `/nobs <your prompt>`. |
| [interview](commands/interview.md) | Stress-tests thinking on a spec, proposal, or idea. Interviews to find gaps, ambiguities, contradictions, and unstated assumptions. Usage: `/interview <name> <topic or paste spec>`. |

---

## Installation

### Claude Code

**Option 1: Copy what you need**

Skills (directory):

```bash
# Available in all your projects
cp -r skills/humanize ~/.claude/skills/humanize

# Or scoped to a single repo
cp -r skills/humanize .claude/skills/humanize
```

Commands (single file):

```bash
# Available in all your projects
cp commands/nobs.md ~/.claude/commands/nobs.md

# Or scoped to a single repo
cp commands/nobs.md .claude/commands/nobs.md
```

The agent picks skills up on the next conversation. Commands are invocable immediately as `/nobs <prompt>`. No config changes needed.

**Option 2: Clone the whole repo**

```bash
git clone https://github.com/orburleigh/agent-kit.git
```

Then copy what you need, or symlink individual skills into your `.claude/skills/` directory.

### Other agents (Cursor, Copilot, Codex, etc.)

The `SKILL.md` file in each skill directory contains all the instructions. Adapt the content to whatever format your tool expects:

- **Cursor** - paste into a `.cursorrules` file or rule directory
- **Copilot** - add to custom instructions
- **Codex** - include in your agent's system context

The principles and reference files are agent-agnostic. Only the loading mechanism differs between tools.

---

## Learn more

New to skills? [agentskills.io](https://agentskills.io) covers the format, frontmatter, and authoring patterns in detail.

---

## Contributing

If you've built a skill that solves a real problem, open a PR. Keep the directory structure consistent and include a README that explains what the skill does and why someone would want it.

---

## License

MIT
