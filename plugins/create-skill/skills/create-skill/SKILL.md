---
name: create-skill
description: Use when creating or restructuring an Agent Skill, converting a slash command into a skill, or making a reusable workflow, checklist, or prompt discoverable to an agent.
---

# Create Skill

Turns a request into a working skill in two stages: an interview that produces an agreed spec, then a build that follows the agentskills.io format. Core principle: every fact in the finished skill traces to the user's answers or verified material. Nothing is invented to fill a gap.

## The iron rule

No skill files are written until the interview is done and the user has approved the spec summary. A baseline test of this exact task showed why: from a one-line request, the agent produced a finished-looking skill containing 13 silent decisions, including invented numeric thresholds and prices recalled from memory that changed between runs.

## Workflow

- [ ] 1. Restate the request in one line. Read references/spec.md.
- [ ] 2. Collision check: list `~/.claude/skills/` and the project's `.claude/skills/`, and scan every loaded skill, plugins and built-ins included. Overlap means the same job, meaning the two skills would produce the same deliverable, not the same moment in a workflow. Clear overlap: propose extending the existing skill and stop. Unclear: raise it as the first interview question rather than deciding silently.
- [ ] 3. Interview (below).
- [ ] 4. Present the spec summary (template below). Wait for explicit approval.
- [ ] 5. Build, following references/spec.md and references/best-practices.md.
- [ ] 6. Validate (checklist below).
- [ ] 7. Offer trigger and output testing; read references/evaluation.md only if the user wants it.

## Interview

Rules:

- One decision point per message; options with a recommended default inside that decision count as one question. Wait for the full answer before the next.
- Reject vague answers. "It should check quality" gets: which checks, against what standard, what happens on failure.
- Go deep before wide. Exhaust an area, then move on.
- Options may be offered, but always with one recommended default.
- An answer the user has not given is a decision the agent may not make silently. It either gets asked, or it goes in the Assumptions list.
- Skip an area only when the user's own words state the answer explicitly; an answer that has to be inferred is not an answer. The interview ends when the spec summary can be filled without invention, not when every question has been recited.
- If the user says "just build it" or "I'm sure", stop asking, build, and list every remaining gap under Assumptions.

Areas, in order:

1. **Job and trigger.** What task, precisely? What would the user actually type when wanting it? What nearby requests must NOT trigger it?
2. **Knowledge source.** Where does the expertise come from: a task recently done, docs, runbooks, corrections the user keeps repeating? Ask for the material itself. If the answer is "general knowledge", say plainly that the skill will add little beyond model defaults and ask whether it is worth building.
3. **Workflow.** The steps in order. Which parts are fragile and need exact commands, which are judgement calls. Where several tools could work, which is the default.
4. **Gotchas.** What would an agent get wrong without being told? The non-obvious facts are the highest-value content in the skill.
5. **Inputs and outputs.** Formats in, format out. Ask for one concrete example of good output to turn into a template.
6. **Numbers and facts.** Thresholds, limits, versions, prices, paths. Each one comes from the user or a named source. None are invented.
7. **Scripts.** Deterministic steps worth bundling as tested scripts. Dependencies and environment constraints.
8. **Boundaries and placement.** What the skill does not do. Personal (`~/.claude/skills/`) or project (`<repo>/.claude/skills/`)?

## Spec summary template

```
Name: <name>            (passes name rules in references/spec.md)
Job: <one line>
Description draft: <the frontmatter text>
Triggers: <3 should-trigger phrasings; 2 near-misses that must not>
Workflow: <numbered outline>
Gotchas: <list>
Files: <SKILL.md only, or + references/scripts/assets, with reason>
Assumptions: <every decision made without an explicit answer>
```

## Build rules

- Structure and hard constraints: references/spec.md. Non-negotiable: name matches directory and the naming rules; description under 1024 characters, triggering conditions only, never a workflow summary; SKILL.md under 500 lines; heavy material moved to references/ with an explicit load trigger ("read X when Y").
- Content: references/best-practices.md. Only what the agent would get wrong without it, defaults not menus, procedures over declarations, gotchas inline, templates for output formats.
- Write for a stranger: the skill must work for an agent with no access to this conversation.
- Create the skill directory and its files only. Do not register, mention or trigger the skill from CLAUDE.md; the frontmatter description is the whole invocation mechanism.
- Other hard-trigger skills still apply at build time: if a prose-hygiene skill such as humanize is loaded, invoke it before writing the new SKILL.md.

## Validation checklist

- [ ] Name: lowercase, digits, single hyphens, 1-64 chars, equals directory name
- [ ] Description: under 1024 chars, imperative "Use when...", keywords the user would type, no workflow summary
- [ ] `wc -l SKILL.md` under 500
- [ ] Every referenced file exists; paths relative to the skill root; no `@` links
- [ ] Every number, tool choice and threshold traceable to an answer or the Assumptions list
- [ ] `skills-ref validate <dir>` if installed; otherwise the checks above by hand
- [ ] Fresh-eyes read: could an agent with zero context execute this?

## Red flags

Any of these means stop and return to the workflow:

- About to write a SKILL.md and no interview happened
- A number, tool or scope decision appears that the user never stated and Assumptions does not list
- "The request is clear enough" - the baseline showed a clear-looking request hiding 13 decisions
- "Drafting first gives the user something to react to" - a draft anchors on invented specifics, and the interview becomes the user debugging fabrications instead of stating intent
- "One batch of questions is faster" - batched answers are shallow
- The description field is starting to describe the workflow
