# Evaluating a skill

Distilled from https://agentskills.io/skill-creation/optimizing-descriptions.md and evaluating-skills.md. Load this when testing whether a new skill triggers and performs; not needed while drafting.

## Definitions and execution

Evaluation definitions are ordinary project files. Creating or validating `evals/evals.json` does not launch evaluator agents or add their model usage beyond the current authoring session. Running trigger or output evaluations does, so treat execution as a separate step that requires the user's agreement.

Every distributable skill includes its definitions even when execution is deferred. Record the deferral in the build report instead of deleting the cases.

## Quick verification (minimum bar for every new skill)

1. **Structure**: frontmatter passes the constraints in references/spec.md (`uvx --from skills-ref==0.1.1 agentskills validate ./skill-name` if `uvx` is available).
2. **Trigger sanity check**: try 3-5 realistic prompts manually, mixing should-trigger and should-not-trigger. Use a fresh session or isolated agent context for each prompt so conversation state does not leak between cases.
3. **Output sanity check**: run one real task with the skill in a clean context and read the execution trace, not just the output. Vague instructions show up as the agent trying several approaches; inapplicable instructions show up as the agent following them anyway.

## Trigger evals (when reliability matters)

Build ~20 labelled queries: 8-10 should-trigger, 8-10 should-not-trigger.

- Vary should-trigger queries by phrasing (formal, casual, typos), explicitness (names the domain vs describes the need), detail and complexity. The most useful ones are where the skill helps but the connection is not obvious.
- The best should-not-trigger queries are **near-misses**: share keywords but need something different ("write a python script that reads a csv and uploads rows to postgres" for a CSV-analysis skill). Obviously irrelevant queries test nothing.
- Make queries realistic: file paths, personal context, column names, casual language.

Run each query 3 times (model behaviour is nondeterministic); trigger rate above 0.5 counts as triggering. A query passes when its trigger outcome matches its label.

To iterate on the description without overfitting: split ~60% train / ~40% validation, keep the split fixed, revise only from train failures, and pick the iteration with the best validation pass rate. Broaden when should-triggers fail; sharpen the boundary when near-misses false-trigger. Never paste keywords from failed queries; address the category they represent. Around five iterations is usually enough.

## Output evals (when the skill's outputs matter)

Test cases live in `evals/evals.json` inside the skill directory:

```json
{
  "skill_name": "csv-analyzer",
  "evals": [
    {
      "id": 1,
      "prompt": "I have a CSV of monthly sales in data/sales_2025.csv. Find the top 3 months by revenue and make a bar chart?",
      "expected_output": "A bar chart of the top 3 months by revenue, labeled axes and values.",
      "files": ["evals/files/sales_2025.csv"],
      "assertions": [
        "The output includes a bar chart image file",
        "The chart shows exactly 3 months",
        "Both axes are labeled"
      ]
    }
  ]
}
```

- Start with 2-3 cases; vary phrasing and cover at least one edge case.
- Run each case **with and without the skill** in clean contexts; the delta is the skill's value. When improving an existing skill, baseline against a snapshot of the previous version.
- Start with provisional assertions derived from the approved contract. After seeing the first with-skill and without-skill outputs, calibrate them: good assertions are verifiable ("valid JSON", "at least 3 recommendations"); bad ones are vague ("output is good") or brittle (exact phrasing). Style and feel belong to human review, not assertions.
- Grade PASS/FAIL with concrete evidence quoted from the output. A section titled "Summary" containing one vague sentence is a FAIL for "includes a summary".
- Analyse patterns: drop assertions that always pass in both configurations (the model does not need the skill for them), fix ones that always fail in both, study the with-skill-only passes to learn what is working, tighten instructions where results are inconsistent across runs.
- Iterate: feed failed assertions, human feedback and execution traces back into the SKILL.md. Generalise fixes rather than patching for one test case; keep the skill lean; explain why rather than stacking ALWAYS/NEVER rules; bundle logic the agent keeps reinventing into scripts. Stop when feedback comes back empty or improvement stalls.

When evaluations run, record the model and harness, pass count, consumed tokens and elapsed time for both configurations. Accuracy shows whether the skill improves the result; tokens and elapsed time show whether it improves efficiency.
