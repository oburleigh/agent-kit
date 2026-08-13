# Skill authoring best practices

Distilled from https://agentskills.io/skill-creation/best-practices.md, optimizing-descriptions.md and using-scripts.md. Re-fetch those URLs if this looks stale.

## Ground the skill in real expertise

A skill generated from general LLM knowledge produces vague, generic procedures ("handle errors appropriately"). Effective skills capture what the agent could not already know. Source material, in order of value:

- A real task completed in conversation: the steps that worked, the corrections the user made, the input/output formats, the context the agent lacked
- Internal docs, runbooks, style guides, API specs, schemas, config files
- Code review comments and issue trackers (recurring concerns)
- Version control history, especially fixes
- Real failure cases and their resolutions

If none of this exists, say so: the skill will only be as good as the agent's general knowledge, and may not be worth building.

## Spend context wisely

- **Add what the agent lacks, omit what it knows.** No explaining what a PDF is or how HTTP works. Test each piece of content with: "Would the agent get this wrong without this instruction?" If no, cut it.
- **Coherent units.** Scope a skill like a function: one coherent unit of work that composes with other skills. Too narrow forces multiple skills to load per task; too broad makes activation imprecise.
- **Moderate detail.** Concise stepwise guidance with one working example outperforms exhaustive documentation. Covering every edge case usually means most are better left to the agent's judgment.
- **Progressive disclosure for large skills.** SKILL.md under 500 lines / 5000 tokens. Move heavy reference to `references/` and state the load trigger: "Read references/api-errors.md if the API returns a non-200 status."

## Calibrate control

- **Freedom where variation is fine.** Describe what to look for, explain why, let the agent choose how. Agents that understand purpose make better context-dependent decisions.
- **Prescriptive where fragile.** Exact commands, exact sequence, "do not modify or add flags" when consistency matters or operations are fragile.
- **Defaults, not menus.** Pick one tool or approach and mention alternatives only as an escape hatch ("Use pdfplumber; for scanned PDFs use pdf2image with pytesseract").
- **Procedures over declarations.** Teach how to approach the class of problem, not the answer to one instance. Details like output templates and hard constraints are fine; the approach must generalise.

## Instruction patterns

- **Gotchas section.** Often the highest-value content: environment-specific facts that defy reasonable assumptions ("the users table uses soft deletes; queries must include WHERE deleted_at IS NULL"). Keep gotchas in SKILL.md, not references, because the agent will not know when to load a file it does not know it needs. Every correction the user makes during use should become a gotcha.
- **Templates for output format.** A concrete template beats prose description; agents pattern-match structures well. Short templates inline, long ones in `assets/`.
- **Checklists for multi-step workflows**, especially with dependencies or validation gates.
- **Validation loops.** Do the work, run a validator (script, checklist or reference), fix, repeat until it passes.
- **Plan-validate-execute** for batch or destructive operations: produce a structured plan, validate it against a source of truth with a script that gives self-correcting error messages, only then execute.
- **Bundle repeated work.** If execution traces show the agent reinventing the same logic each run, write it once as a tested script in `scripts/`.

## Descriptions that trigger reliably

The description is the only thing loaded at startup; it carries the entire triggering burden.

- **Imperative phrasing**: "Use when..." not "This skill does...".
- **User intent, not implementation.** Match against what users ask for, not internal mechanics.
- **Be pushy.** List contexts where it applies, including when the user does not name the domain: "even if they don't explicitly mention CSV or analysis."
- **Include keywords** users would actually type: file types, error messages, tool names, task verbs.
- **Do not summarise the skill's internal workflow.** An agent may follow the description shortcut instead of reading the body. Triggering conditions only.
- **Concise.** A few sentences. Hard limit 1024 characters.

Before/after example:

```yaml
# Before
description: Process CSV files.

# After
description: >
  Analyze CSV and tabular data files: compute summary statistics,
  add derived columns, generate charts, and clean messy data. Use
  when the user has a CSV, TSV, or Excel file and wants to explore,
  transform, or visualize the data, even if they don't explicitly
  mention "CSV" or "analysis."
```

To test triggering properly, see references/evaluation.md.

## Scripts

One-off commands: reference existing packages directly (`uvx ruff@0.8.0 check .`, `npx eslint@9 --fix .`). Pin versions. State prerequisites in SKILL.md or the `compatibility` field. When a command grows hard to get right first try, promote it to a tested script in `scripts/`.

Bundled scripts should declare dependencies inline so one command runs them: PEP 723 blocks run via `uv run scripts/x.py`; Deno `npm:` specifiers; Bun auto-install; Ruby `bundler/inline`.

Design for agentic use:

- **Never prompt interactively.** Agents run non-interactive shells; a TTY prompt hangs forever. All input via flags, env vars or stdin. Missing input fails with usage guidance.
- **`--help` is the interface contract**: description, flags, examples, kept short.
- **Error messages shape the retry**: say what went wrong, what was expected, what to try. "Error: --format must be one of: json, csv, table. Received: xml."
- **Structured output** (JSON/CSV/TSV) to stdout, diagnostics to stderr.
- **Idempotent** (agents retry), **dry-run for destructive ops**, **distinct exit codes**, **bounded output size** (harnesses truncate around 10-30K chars; default to summaries, support --offset or --output).

List bundled scripts in SKILL.md under an "Available scripts" heading with one line each, then reference them by relative path from the skill root.
