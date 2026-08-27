# create-skill

Builds Agent Skills through an interview instead of guesswork. Invoke it explicitly through the installed runtime or ask for a skill in plain language ("create me a skill that...", "turn this workflow into a command").

## Why it exists

Asked to create a skill from a one-line request, an agent fills every gap with plausible invention. In baseline testing that meant 13 silent decisions in one skill, including made-up thresholds and prices recalled from memory. This skill replaces invention with questions.

## What happens on invocation

1. The request is restated and checked against every existing skill for overlap.
2. An interview runs, one decision at a time: the job and its triggers, where the expertise comes from, workflow, gotchas, inputs and outputs, every number, scripts, boundaries and placement. Vague answers get pushed back on. "Just build it" ends the questioning and logs remaining gaps as assumptions.
3. A spec summary (name, description, triggers, workflow, gotchas, file plan, assumptions) is presented for approval. Nothing is written before that approval.
4. The skill is built to the agentskills.io format, validated against a checklist, and offered for trigger and output testing.

## Files

| File | Purpose |
| --- | --- |
| `SKILL.md` | The workflow, interview protocol and validation checklist |
| `references/spec.md` | The agentskills.io format specification, distilled |
| `references/best-practices.md` | Authoring guidance: scoping, context economy, descriptions, scripts |
| `references/evaluation.md` | Trigger and output evaluation methods, loaded only when testing |
