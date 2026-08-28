# Agent Skills format specification

Distilled from https://agentskills.io/specification.md. When in doubt, or if this file looks stale, re-fetch that URL and https://agentskills.io/llms.txt.

## Directory structure

A skill is a directory containing, at minimum, a SKILL.md file:

```
skill-name/
├── SKILL.md          # Required: metadata + instructions
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation loaded on demand
├── assets/           # Optional: templates, images, data files
└── ...
```

## Frontmatter fields

| Field           | Required | Constraints |
| --------------- | -------- | ----------- |
| `name`          | Yes      | 1-64 chars. Lowercase letters, numbers, hyphens only. No leading/trailing hyphen. No consecutive hyphens (`--`). Must match the parent directory name. |
| `description`   | Yes      | 1-1024 chars, non-empty. What the skill does and when to use it, with keywords agents would match against. |
| `license`       | No       | Short: a license name or a pointer to a bundled license file. |
| `compatibility` | No       | 1-500 chars. Only when the skill has environment requirements (product, system packages, network access). Most skills do not need it. |
| `metadata`      | No       | Arbitrary string-to-string map. Use reasonably unique key names. |
| `allowed-tools` | No       | Space-separated pre-approved tools, e.g. `Bash(git:*) Read`. Experimental; support varies by client. |

Minimal valid example:

```markdown
---
name: pdf-processing
description: Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction.
---
```

Invalid names: `PDF-Processing` (uppercase), `-pdf` (leading hyphen), `pdf--processing` (consecutive hyphens).

## Body content

Markdown after the frontmatter. No format restrictions. Recommended sections: step-by-step instructions, examples of inputs and outputs, common edge cases.

The whole file loads once the skill activates, so keep it lean and split long content into referenced files.

## Optional directories

- `scripts/` - executable code. Self-contained or with documented dependencies, helpful error messages, graceful edge-case handling.
- `references/` - documentation loaded on demand. Keep individual files focused; smaller files mean less context use.
- `assets/` - templates, images, lookup tables, schemas.

## Progressive disclosure

Agents load skills in three levels:

1. **Metadata** (~100 tokens): `name` and `description` load at startup for all skills. The description carries the entire triggering burden.
2. **Instructions** (< 5000 tokens recommended): the full SKILL.md body loads when the skill activates. Keep SKILL.md under 500 lines.
3. **Resources** (as needed): files in `scripts/`, `references/`, `assets/` load only when required. Tell the agent *when* to load each file ("Read references/api-errors.md if the API returns a non-200 status"), not a generic "see references/".

## File references

Use relative paths from the skill root: `references/REFERENCE.md`, `scripts/extract.py`. Keep references one level deep from SKILL.md; avoid nested reference chains. Never use `@` force-load links; they consume context immediately.

## Placement by target runtime

Choose the scope before naming a destination. For each target runtime, the collision check has two parts: the active catalog, including built-ins and loaded plugins, followed by its personal and current-project Agent Skills directories. The chosen scope controls the destination:

| Scope | Codex | Claude |
| --- | --- | --- |
| Personal | `~/.agents/skills/<name>/`; also check `$CODEX_HOME/skills/<name>/` when configured, otherwise `~/.codex/skills/<name>/`, for an existing skill | `~/.claude/skills/<name>/` |
| Project-level | `<repo>/.agents/skills/<name>/` | `<repo>/.claude/skills/<name>/` |
| Distributable plugin | `<plugin>/skills/<name>/` | `<plugin>/skills/<name>/` |

For Codex collision checks, include `~/.agents/skills/`, any configured legacy personal directory, and every `.agents/skills/` directory from the current working directory through the repository root. For Claude, include `~/.claude/skills/` and the current project's `.claude/skills/`. For more than one target runtime, inspect both sets. If the requested scope is personal or project-level, ask whether the user wants separate copies or one distributable plugin. Do not write separate copies unless the user chooses them.

## Validation

```bash
skills-ref validate ./my-skill
```

From https://github.com/agentskills/agentskills/tree/main/skills-ref. If not installed, check the frontmatter constraints above by hand: name regex, description length, name matches directory.
