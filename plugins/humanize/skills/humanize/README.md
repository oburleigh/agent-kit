# Humanize

A skill that strips AI-generated writing patterns from professional artifacts. Documentation, analysis, PR descriptions, commit messages, reports - anything an AI agent produces that a human will read.

## The problem

AI-generated text is obvious. Readers spot it within a paragraph. The vocabulary is inflated ("leverage," "utilize," "facilitate"), every topic gets treated as equally significant, sentences march along at the same length, and the structure follows the same template regardless of content type. This makes the output feel generic and erodes trust.

## What this skill does

When an AI agent writes any artifact, this skill catches the patterns that make it read like a machine wrote it and rewrites them. It targets specific problems:

- **Vocabulary inflation** - swaps words like "utilize" for "use," "facilitate" for "help," "paramount" for "important." The full list lives in `references/ai-patterns.md` with over 60 flagged words and their replacements.
- **Flat rhythm** - breaks up the uniform 25-30 word sentence length that AI defaults to. Short sentences hit harder. Longer ones work when the idea needs room.
- **Hedging** - cuts the qualifier stacking ("could potentially possibly improve") down to a single clear statement of uncertainty when uncertainty actually exists.
- **Significance inflation** - stops treating a config change like a turning point in software history.
- **Structural defaults** - picks the right format for the content (numbered steps for procedures, prose for explanations, tables for reference material) instead of applying bullet lists to everything.
- **Formulaic openings and closings** - kills "In today's fast-paced..." and "In conclusion..." dead.

The skill also maintains a corrections log. When a user rewrites something the skill produced, that feedback gets recorded in `references/corrections.md` and folded back into the skill once enough patterns accumulate.

## Installation

Install the complete Agent Kit plugin or the standalone `humanize` plugin. See the [Agent Kit installation guide](../../../../README.md) for Codex and Claude Code commands.

The skill expects this structure:

```
humanize/
  SKILL.md              # The skill definition
  README.md             # This file
  references/
    ai-patterns.md      # Vocabulary and structural patterns catalog
    corrections.md      # User feedback log
  evals/
    evals.json          # Evaluation tests
```

## How it works

The skill activates whenever the agent produces a written artifact. It runs through a checklist:

1. Check `references/corrections.md` for recent feedback
2. Draft the content following plain-language principles
3. Cross-check against `references/ai-patterns.md` for patterns that slipped through
4. Re-read for anything that sounds like it could appear in a generic AI blog post
5. Verify the structure fits the content type, not a template

The test for success: could a specific person with real expertise have written this? If the text could apply to any topic with a few noun swaps, it failed.

## Scope

This applies to produced artifacts only. Chat messages, conversational replies, and quick answers are out of scope. The skill targets documents, guides, reports, PR descriptions, commit messages, and anything else that gets read as a finished piece of writing.

## References

- `references/ai-patterns.md` - full catalog of flagged vocabulary, phrases, and structural patterns
- `references/corrections.md` - running log of user feedback, pruned after 15 entries
