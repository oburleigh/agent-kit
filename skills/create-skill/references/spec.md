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

## Validation

```bash
skills-ref validate ./my-skill
```

From https://github.com/agentskills/agentskills/tree/main/skills-ref. If not installed, check the frontmatter constraints above by hand: name regex, description length, name matches directory.
