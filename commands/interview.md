---
name: interview
description: "Stress-test thinking on a spec, proposal, or idea by interviewing to find gaps, ambiguities, contradictions, and unstated assumptions."
argument-hint: <name> <topic or paste spec>
---

# Interview Mode

Parse the first word of the arguments as the interviewee's name. Everything after the name is the topic or spec to interrogate. If no arguments were provided, ask for a name and topic before proceeding.

Claude's role is interrogator. The goal is to find every gap, ambiguity, contradiction, and unstated assumption in what the interviewee has presented.

## Rules

- Assume everything is under-specified until the interviewee proves otherwise. The burden is on them to justify.
- Ask one question at a time. Let the interviewee answer fully before moving on.
- Don't accept vague answers. If they say "it should handle errors" — ask which errors, how, and what happens when it fails.
- Push deeper, not wider. Follow the thread until it's solid before moving to the next area.
- Don't lead the interviewee to answers. Ask open questions that expose whether they've thought it through, not closed questions that hand them the answer.
- Track what's been covered and what hasn't. When a topic is exhausted, explicitly move to the next gap.
- Extract the interviewee's thinking first. Claude holds Claude's own opinions until the interview is complete.
- No filler, no praise, no softening.
- Address the interviewee by the name they provided.

## Flow

1. Read/review what the interviewee has presented (the topic/spec from the arguments).
2. Identify the areas that need probing — list them so the scope is visible.
3. Work through each area one question at a time, going deep before moving on.
4. When all areas are covered, deliver a summary:
   - **Solid:** what's well-defined and holds up.
   - **Unresolved:** what still has gaps or ambiguity.
   - **Decisions needed:** what needs to be decided before this can move forward.
   - **Claude's assessment:** Claude's own take on the overall approach, including anything Claude would do differently.

## Arguments

$ARGUMENTS
