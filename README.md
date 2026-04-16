# agent-kit

Skills, commands, and resources that make AI coding agents better at their job. Works with Claude Code, Cursor, Copilot, Codex, and anything else that accepts structured instructions.

This is a living collection. Each skill is tested in real workflows before it lands here.

---

## Quick nav

**[Skills](#skills)** | **[Commands](#commands)** | **[Installation](#installation)** | **[Writing your own](#writing-your-own)** | **[Contributing](#contributing)**

---

## Skills

Skills are packaged instructions that teach an agent how to handle a specific task well. Not a one-line system prompt. Each one includes the reasoning behind its rules, reference material the agent can look up at runtime, and enough edge-case coverage that the agent doesn't fall apart when things get messy.

| Skill | Description |
|-------|-------------|
| [humanize](skills/humanize/) | Catches and rewrites AI writing patterns in docs, PRs, commit messages, and reports. Maintains a 60+ word blacklist, detects structural tics, and learns from corrections over time. |
| [git-commit](skills/git-commit/) | Produces clean git commits following Conventional Commits v1.0.0. Checks branch protection, stages files selectively, splits unrelated changes into separate commits, and respects project-specific conventions. |

## Commands

Slash commands and shorter task-specific instructions. This section is growing.

---

## Installation

### Claude Code

**Option 1: Copy the skill directory**

```bash
# Available in all your projects
cp -r skills/humanize ~/.claude/skills/humanize

# Or scoped to a single repo
cp -r skills/humanize .claude/skills/humanize
```

The agent picks it up on the next conversation. No config changes needed.

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

## New to agent skills?

Most AI coding tools let you give the agent extra instructions beyond the default system prompt. Claude Code calls these "skills." Cursor calls them "rules." Copilot has "custom instructions." Different names, same idea: a file the agent reads at startup that changes how it works.

A bare prompt like "write good commit messages" gives the agent almost nothing to work with. A skill like `git-commit` gives it the Conventional Commits spec, branch protection checks, a staging workflow, message templates, and the reasoning behind each step. The difference in output quality is significant.

Skills in this repo follow a common structure:

```
skill-name/
  SKILL.md              # What the agent loads (required)
  README.md             # Human-readable docs
  references/           # Material the skill reads at runtime
  evals/                # Tests to verify the skill works
```

`SKILL.md` is the only required file. Everything else supports it.

---

## Writing your own

A skill is a markdown file with YAML frontmatter. The frontmatter tells the agent when to activate:

```yaml
---
name: my-skill
description: One line explaining when to trigger this. Be specific or the agent will fire it too often or ignore it entirely.
---
```

The body contains the actual instructions. A few things that separate good skills from bad ones:

**Explain the why, not just the what.** An agent that understands the reasoning behind a rule handles edge cases on its own. One that's following a rigid checklist breaks the moment something unexpected happens.

**Include reference material.** If the skill needs a vocabulary list, a template, or a set of examples, put them in a `references/` directory. The agent can read them at runtime instead of you cramming everything into one file.

**Define what success looks like.** If the agent can self-check its output against a clear standard, it catches its own mistakes before you have to.

**Write the description carefully.** The one-line `description` field in the frontmatter is what determines whether the agent activates the skill. Vague descriptions like "helps with code" mean it triggers on everything or nothing. "Creates git commits following Conventional Commits v1.0.0 when the user asks to commit or stage changes" tells the agent exactly when to fire.

---

## Contributing

If you've built a skill that solves a real problem, open a PR. Keep the directory structure consistent and include a README that explains what the skill does and why someone would want it.

---

## License

MIT
