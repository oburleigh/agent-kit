---
name: humanize
description: Use when writing or revising substantial professional prose, including documentation, guides, analyses, reports, summaries, pull request descriptions, and commit messages.
---

# Humanize

## Purpose

AI-generated text has recognizable patterns that make it immediately identifiable to readers. Specific vocabulary choices, structural tics, and formatting habits signal "a machine wrote this" before the reader has finished the first paragraph. This erodes trust and makes the content feel generic.

This skill eliminates those patterns from professional written artifacts: technical documentation, analysis, research, reports, summaries, and guides. The goal is writing that reads like it came from a knowledgeable professional who actually cares about the subject.

**Scope:** Produced artifacts only. This does not apply to conversational chat.

## Principles

### Use plain language

The strongest indicator of AI writing is vocabulary inflation, using elaborate words where simple ones work. AI models default to words like "delve," "crucial," "leverage," "utilize," "facilitate," "robust," "seamless," "pivotal," and "comprehensive" because they appear frequently in training data as "impressive-sounding" filler. Human professionals use them rarely, and only when the specific meaning is needed.

The fix: use the simplest word that's accurate. "Use" not "utilize." "Help" not "facilitate." "Important" not "paramount." "Show" not "illuminate." If a word sounds like it belongs in a press release, replace it.

See `references/ai-patterns.md` for the full vocabulary list. Read it when writing any artifact to check vocabulary choices.

### Vary sentence rhythm

AI text has a metronomic quality. Sentences tend toward uniform length, averaging 25-30 words. Real writing mixes short punchy sentences with longer ones. A three-word sentence after a complex one creates emphasis. Monotonous rhythm is the written equivalent of speaking in a flat tone.

Aim for variety. Some sentences should be under 10 words. Some can run longer when the idea demands it. Let the content dictate the structure, not a template.

### Be direct, drop the hedging

AI text hedges constantly: "it could potentially," "more often than not," "to some extent," "from a broader perspective." This reads as evasive. Professional writing takes positions. If something is true, say it is. If there's genuine uncertainty, state the uncertainty once and clearly. Don't sprinkle qualifiers across every sentence.

Similarly, avoid the pattern of presenting every topic as equally significant. Not everything "plays a vital role" or "serves as a cornerstone." Some things matter more than others. Say so.

### Don't inflate significance

AI text treats every subject like it's the most important thing in the world. Everything "marks a pivotal moment," "stands as a testament," "underscores the importance," or "continues to captivate." This is the written equivalent of speaking entirely in exclamation marks. When everything is significant, nothing is.

Describe things proportionally. A minor API change is a minor API change, not a "groundbreaking shift in the developer experience landscape."

### Match structure to content

The problem with AI formatting is not that it uses structure. The problem is that it applies the same structure to everything regardless of content type. The fix is to choose the right format for what the content actually is.

**Procedural content (guides, setup docs, onboarding, tutorials):** Use numbered steps for sequential actions and headings for distinct phases. A getting-started guide with three setup steps should be a numbered list under a heading, not a prose paragraph that buries the steps in running text. Readers scan procedural docs for "what do I do next" and structure helps them find it.

**Explanatory content (architecture docs, analysis, research):** Prose paragraphs are usually the right default. Use headings to break up long sections by topic. Bullet lists work for genuinely parallel items but should not be the primary vehicle for explanation.

**Reference content (API docs, changelogs, config references):** Tables, definition lists, and structured formats are appropriate here. This is inherently structured content.

What to avoid across all content types:
- The bold-term-colon-restatement pattern ("**Scalability:** The system is designed to scale..."). If a term needs defining, weave it into prose or use a proper definition structure.
- The rule of three. Not every list needs exactly three items and not every description needs three adjectives. Use the number the content actually requires.
- Bookending every section with an introduction and summary. Short sections don't need either.

### Kill the formulaic openings and closings

Never open with:
- "In today's fast-paced..." / "In the dynamic world of..." / "In today's [anything]"
- "Have you ever wondered..." / "Are you struggling with..."
- "In the realm of..." / "When it comes to..."

Never close with:
- "In conclusion..." / "In summary..." / "Overall..."
- "The future looks bright" or any variation of optimistic crystal-balling
- Restating what was just said in a "summary" paragraph for content under 1,000 words

Start with the substance. End when the substance is done.

### Avoid structural gimmicks

These constructions appear in AI text at rates far higher than human writing:

- **Negative parallelism:** "It's not X, it's Y" / "Not only X but Y". Used occasionally by humans, but AI leans on it as a primary rhetorical device.
- **False range:** "From X to Y" constructions that imply a spectrum but are really just two things stuck together ("from intimate gatherings to global movements").
- **Participial phrase chains:** Sentence + comma + "-ing phrase" used to tack on hollow commentary ("...reflecting the company's commitment to innovation"). AI models use these at 2-5x the rate of human writers. If the -ing phrase adds real information, keep it. If it's padding, cut it.
- **Copula avoidance:** Using "serves as," "functions as," "marks the" instead of "is." Just say "is."
- **Synonym cycling:** Referring to the same thing as "the platform," "the solution," "the system," "the tool" across consecutive sentences to avoid repetition. Pick one term and stick with it. Repetition is fine.

### Format with restraint

- **Em dashes and double hyphens:** Never use em dashes (`—`) or double hyphens (`--`) in artifacts. Both are AI tells. If a sentence needs a parenthetical aside, use a comma, a single hyphen with spaces (` - `), parentheses, or split it into two sentences. Restructuring is almost always better than reaching for a dash.
- **Bold text:** Reserve for genuinely critical terms or warnings, not as a visual structure for every paragraph.
- **Emoji:** Never in professional artifacts.
- **Lists and structure:** Use headings, numbered steps, and bullet lists when the content is genuinely procedural, parallel, or benefits from scanning. Procedural docs should have clear steps. Reference material should have clear headings. The problem is not structure itself but using lists and formatting as a default when prose would be clearer. Match the format to the content.

### Revision behavior

When revising or updating a document, make the changes directly. Do not add commentary about what changed within the document itself. No "As discussed," "Updated to reflect," "The following section has been revised to," or any meta-narrative about the editing process. The document should read as if it was always written this way.

If the reader needs to know what changed, that belongs in a changelog or commit message, not in the body of the document.

### PR descriptions and commit summaries

PR descriptions are one of the most visible places AI writing patterns show up. Common AI tells in PRs:

- Opening with "This PR..." followed by a grandiose verb ("introduces," "implements," "establishes," "enhances"). Just say what changed.
- Treating every change as significant. A config tweak is a config tweak, not a "refinement of the deployment pipeline."
- Bullet lists that restate every file changed. The diff already shows that. Summarise what changed and why, not a file-by-file inventory.
- Closing with "This ensures..." or "This improves..." followed by a vague benefit. If there's a concrete benefit, state it. If not, leave it out.

A good PR description says what changed, why it changed, and anything a reviewer needs to know that isn't obvious from the code. Write it the way you'd explain the change to a colleague in a few sentences.

**Bad:**
> This PR introduces a comprehensive refactoring of the authentication middleware, enhancing security posture and streamlining the token validation pipeline. Key changes include JWT verification improvements, session handling optimizations, and robust error propagation.

**Good:**
> Moved auth from session cookies to JWTs. The old session store was hitting memory limits under load. JWT validation happens in middleware now so individual routes don't need to check auth themselves. Still need to migrate the admin endpoints in a follow-up.

## When writing an artifact

1. Resolve the persistent config root below. Read `humanize/rules.md` and `humanize/corrections.md` from it when they exist.
2. Draft the content following the principles above.
3. Read `references/ai-patterns.md` to check for vocabulary and structural patterns that slipped through.
4. Read the draft with fresh eyes. Rewrite anything that sounds like a generic AI-generated blog post.
5. Check that the structure fits the content instead of a template.

The strongest test: could this have been written by a specific person with expertise in this area? Generic text that could apply to any topic is the core failure mode.

## Learning from corrections

Never write to files inside the installed skill. Plugin files are bundled references and may be read-only or replaced during an update.

Resolve one persistent config root for every supported agent runtime:

1. Use `AGENT_KIT_CONFIG_HOME` when it contains a non-empty absolute path. If it is set but invalid, ask the user to correct it instead of silently choosing another root.
2. On Windows, use `%APPDATA%\agent-kit` when `APPDATA` is an absolute path.
3. On Unix, use `$XDG_CONFIG_HOME/agent-kit` when `XDG_CONFIG_HOME` is a non-empty absolute path. Ignore a relative `XDG_CONFIG_HOME` and fall back to `$HOME/.config/agent-kit` when `HOME` is absolute.
4. Resolve existing symlinks, or the nearest existing parent, and confirm the root is outside the installed skill and plugin caches. Reject a root that points into either location.

If no candidate passes these checks, ask the user to set `AGENT_KIT_CONFIG_HOME` to a valid root. Do not fall back to a plugin cache, installed skills directory, working directory, or runtime-specific memory directory.

Keep learned state under that root:

- `humanize/rules.md` contains durable rules promoted from repeated feedback.
- `humanize/corrections.md` contains the recent correction log.

Resolve the `humanize` directory and each state path, or its nearest existing parent, immediately before every read or write. Reject symbolic links, junctions, or other paths that resolve outside the resolved config root or into an installed skill or plugin cache.

Apply user corrections to the current artifact. A correction alone is not permission to persist it. Write learned state only when the user asks you to remember the correction or confirms persistence after you ask. If they do neither, leave the config files unchanged.

After explicit consent, create the `humanize` directory and corrections file if needed. Start a new corrections file with `# Humanize corrections`, then append the correction with the before, after, and general pattern. Preserve existing entries and do not write secrets or unrelated conversation content.

Format each entry as:
```
## YYYY-MM-DD: Short description
**Before:** What the agent wrote
**After:** What the user preferred
**Pattern:** The general rule to extract
```

### Pruning the corrections log

Do not prune automatically. When the persistent `humanize/corrections.md` has more than 15 entries, propose a cleanup and ask for approval. After approval:

1. Read through all corrections and identify repeated patterns
2. Add repeated patterns to the persistent `humanize/rules.md`
3. Move the processed entries to a dated file under `humanize/archive/`
4. Remove only the archived entries from the active corrections log

Keep one-off corrections in the archive rather than deleting them. If the user declines cleanup, leave every file unchanged.
