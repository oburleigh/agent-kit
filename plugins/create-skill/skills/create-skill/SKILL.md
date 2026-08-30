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
- [ ] 2. Collision check: inspect the active skill catalog, including built-ins and loaded plugins. If the target runtime and placement are already known, also inspect the matching Agent Skills directories in references/spec.md. Otherwise finish the placement interview before checking filesystem locations. Check the target runtime, not only the runtime executing this workflow. Overlap means the same job, meaning the two skills would produce the same deliverable, not the same moment in a workflow. Clear overlap: propose extending the existing skill and stop. Unclear: raise it as the first interview question rather than deciding silently.
- [ ] 3. Interview (below).
- [ ] 4. Present the spec summary (template below). Wait for explicit approval.
- [ ] 5. Build, following references/spec.md and references/best-practices.md.
- [ ] 6. For a distributable skill, read references/evaluation.md and create `evals/evals.json` from the approved evaluation contract.
- [ ] 7. Validate (checklist below).
- [ ] 8. Offer to run trigger and output evaluations. Creating definitions does not launch evaluator agents or add their model usage beyond the current authoring session; execution requires separate approval.

## Interview

Rules:

- One decision point per message; options with a recommended default inside that decision count as one question. Wait for the full answer before the next.
- Reject vague answers. "It should check quality" gets: which checks, against what standard, what happens on failure.
- Go deep before wide. Exhaust an area, then move on.
- Options may be offered. Recommend a default only when it follows from the user's answers or a verified source; otherwise say there is no grounded default.
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
7. **Scripts.** Deterministic steps worth bundling as tested scripts. Capture the stable execution command, inputs, structured result, bounded diagnostics, exit-code meanings, success evidence and the failure evidence that would justify inspecting implementation. For batch, create or destructive work, also capture a read-only plan command and structured plan separately from the execution result. Dependencies and environment constraints.
8. **Evaluation.** What observable behaviour proves the skill helps? Capture realistic prompts, expected outcomes and verifiable assertions. Ask whether model-backed execution is approved now or deferred; deferral does not remove evaluation definitions from a distributable skill.
9. **Boundaries and placement.** What the skill does not do. First ask whether it is personal, project-level, or a distributable plugin. If scope is known but runtime is not, ask "Which agent runtimes must support it: Codex, Claude, or both?" and stop. The runtime executing this workflow is not a recommended default. If both runtimes are selected for a personal or project-level skill, ask whether to create separate runtime-specific copies or change the scope to a distributable plugin, then stop without naming either destination. Recommend the plugin when one installable package must serve both. Once these answers are known, name the exact directory or directories from references/spec.md.

## Spec summary template

```
Name: <name>            (passes name rules in references/spec.md)
Job: <one line>
Description draft: <the frontmatter text>
Triggers: <3 should-trigger phrasings; 2 near-misses that must not>
Workflow: <numbered outline>
Gotchas: <list>
Script contract: <execution command, inputs, structured result, diagnostics, exits, success evidence and inspection condition; include a distinct read-only plan command and plan schema for batch, create or destructive work; or none>
Evaluation: <realistic prompts, expected outcomes, assertions, and whether model-backed execution is approved or deferred>
Runtimes: <Codex, Claude, or both>
Placement: <personal, project-level, or distributable plugin, followed by the resolved directory>
Files: <SKILL.md only, or + references/scripts/assets, with reason; distributable skills also include evals/evals.json>
Assumptions: <every decision made without an explicit answer>
```

## Build rules

- Structure and hard constraints: references/spec.md. Non-negotiable: name matches directory and the naming rules; description under 1024 characters, triggering conditions only, never a workflow summary; SKILL.md under 500 lines; heavy material moved to references/ with an explicit load trigger ("read X when Y").
- Content: references/best-practices.md. Only what the agent would get wrong without it, defaults not menus, procedures over declarations, gotchas inline, templates for output formats.
- Write for a stranger: the skill must work for an agent with no access to this conversation.
- Use the selected runtime and placement row in references/spec.md. Do not place a skill for the runtime executing this workflow unless that is also the user's target.
- Before any write, complete a collision result with two parts: `Active catalog` covers built-ins and loaded plugins; `Filesystem` covers the target runtimes' personal and current-project Agent Skills directories.
- Treat bundled scripts as command interfaces. A successful deterministic result and documented exit status are verification evidence; do not read implementation unless changing it or focused failure evidence requires inspection. Batch, create and destructive scripts expose a read-only plan from the same resolution logic and distinguish its schema from the execution result.
- Every distributable skill includes `evals/evals.json` using references/evaluation.md. Defining cases does not launch evaluator agents or add their model usage. If evaluation execution is deferred, keep the definitions and report the deferral.
- Create only the requested skill files. Do not register or trigger the skill from repository instruction files. Frontmatter and package manifests own discovery.
- Other hard-trigger skills still apply at build time: if a prose-hygiene skill such as humanize is loaded, invoke it before writing the new SKILL.md.

## Validation checklist

- [ ] Name: lowercase, digits, single hyphens, 1-64 chars, equals directory name
- [ ] Description: under 1024 chars, imperative "Use when...", keywords the user would type, no workflow summary
- [ ] `wc -l SKILL.md` under 500
- [ ] Every referenced file exists; paths relative to the skill root; no `@` links
- [ ] Every number, tool choice and threshold traceable to an answer or the Assumptions list
- [ ] Every distributable skill has `evals/evals.json`; its `skill_name` matches the directory and each case has a unique ID, prompt, expected output and non-empty assertions
- [ ] `uvx --from skills-ref==0.1.1 agentskills validate <dir>` if `uvx` is available; otherwise the checks above by hand
- [ ] Fresh-eyes read: could an agent with zero context execute this?

## Red flags

Any of these means stop and return to the workflow:

- About to write a SKILL.md and no interview happened
- A number, tool or scope decision appears that the user never stated and Assumptions does not list
- "The request is clear enough" - the baseline showed a clear-looking request hiding 13 decisions
- "Drafting first gives the user something to react to" - a draft anchors on invented specifics, and the interview becomes the user debugging fabrications instead of stating intent
- "One batch of questions is faster" - batched answers are shallow
- The description field is starting to describe the workflow
- "The user deferred model evaluations, so the distributable package does not need evaluation definitions" - definitions do not launch evaluator agents
