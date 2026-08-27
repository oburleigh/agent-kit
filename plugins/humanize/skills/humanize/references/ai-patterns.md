# AI Writing Patterns Reference

A catalog of patterns that signal AI-generated text. Organized for quick lookup when reviewing draft artifacts. Sources include Wikipedia's "Signs of AI Writing" guide, huntingthemuse.net, seanjkernan.substack.com, and several secondary analyses.

## Table of Contents

1. [Vocabulary - Words to Avoid](#vocabulary--words-to-avoid)
2. [Phrases to Avoid](#phrases-to-avoid)
3. [Structural Patterns](#structural-patterns)
4. [Formatting Tells](#formatting-tells)

---

## Vocabulary - Words to Avoid

These words spiked in usage after ChatGPT's release and are flagged by AI detection research (Helsinki 2025 study, Wikipedia editorial guidelines). Avoid unless the word's precise meaning is genuinely needed and no simpler alternative exists.

### Tier 1 - Immediate red flags

| Avoid | Use instead |
|---|---|
| delve | explore, examine, look at |
| tapestry | (usually unnecessary - describe the actual thing) |
| crucial | important, key |
| pivotal | important, key, turning point |
| meticulous / meticulously | careful, thorough |
| vibrant | (be specific - what makes it vibrant?) |
| robust | strong, reliable, solid |
| seamless | smooth, easy |
| groundbreaking | new, significant, first |
| leverage | use |
| synergy | (usually unnecessary - describe the actual benefit) |
| transformative | (describe what actually changed) |
| paramount | important, top priority |
| multifaceted | complex, varied |
| myriad | many |
| cornerstone | foundation, basis, core |
| reimagine | redesign, rethink |
| empower | enable, let, allow |
| catalyst | cause, trigger, driver |
| bolster | strengthen, support |
| spearhead | lead |
| invaluable | valuable, essential |
| realm | area, field, domain |
| foster | encourage, support, build |
| garner | get, earn, attract |
| interplay | interaction, relationship |
| intricate / intricacies | complex, detailed |
| harness | use, apply |
| unleash | release, enable |
| revolutionize | change, transform |
| elucidate | explain, clarify |
| encompass | include, cover |
| holistic | complete, whole, full |
| utilize | use |
| facilitate | help, enable |
| nuanced | subtle, detailed |
| paradigm | model, approach, framework |
| underscore | highlight, show, emphasize |
| illuminate | explain, clarify, show |
| elevate | improve, raise |

### Tier 2 - Context-dependent

These are real words with legitimate uses but AI overuses them as intensifiers or filler:

- significant, critical, key, valuable (fine when precise; bad when every item is "significant")
- landscape (as metaphor -"the competitive landscape" is borderline; "the SaaS landscape" is AI-speak)
- innovative, cutting-edge (describe what's actually new instead)
- comprehensive (often padding - what does it actually cover?)
- dynamic (vague - what's actually changing?)
- streamline (overused - say what was simplified)

---

## Phrases to Avoid

### Openings

| Avoid | Why |
|---|---|
| "In today's fast-paced..." | Generic filler. Start with the actual subject. |
| "In the dynamic world of..." | Same. |
| "As the world continues to evolve..." | Same. |
| "Have you ever wondered..." | Rhetorical question opener - reads as clickbait. |
| "Are you struggling with..." | Same. |
| "What if I told you..." | Same. |
| "In the realm of..." | Inflated. Just name the field. |
| "When it comes to..." | Stalling. Get to the point. |

### Transitions and filler

| Avoid | Use instead |
|---|---|
| "It's important to note that" | (Just state the thing.) |
| "It is worth noting" | (Just state the thing.) |
| "Moreover" | also, and, (or restructure) |
| "Furthermore" | also, and, (or restructure) |
| "Additionally" | also, (or start a new sentence) |
| "In order to" | to |
| "Due to the fact that" | because |
| "No discussion would be complete without" | (Just discuss it.) |
| "Based on the information provided" | (Remove - it's filler.) |
| "Generally speaking" | (Remove - just state it.) |
| "From a broader perspective" | (Remove or be specific about whose perspective.) |

### Closings

| Avoid | Why |
|---|---|
| "In conclusion" | The reader can see it's the end. |
| "In summary" | Same - and short pieces don't need summaries. |
| "Overall" | Usually precedes a restatement. Cut it. |
| "The future looks bright" | Hollow optimism. |
| "I hope this helps" | Chatbot leakage - never in artifacts. |
| "Let me know if..." | Same. |

### Significance inflation

| Avoid | Use instead |
|---|---|
| "serves as a testament to" | shows, demonstrates, is |
| "stands as a testament to" | shows, is |
| "plays a vital/significant role in" | is important to, matters for |
| "underscores the importance of" | shows, highlights |
| "continues to captivate" | (describe specific interest or engagement) |
| "marks a pivotal moment in" | was a turning point, changed |
| "rich cultural heritage" | (describe the actual heritage) |
| "breathtaking" | (describe what's actually impressive) |
| "cutting-edge" | (describe what's actually new) |
| "nestled in the heart of" | in, located in |
| "boasts a range of" | has, offers, includes |
| "marking a pivotal step" | (describe what step was taken) |

### Hedging stacks

Avoid stacking qualifiers. One hedge per uncertain claim is enough.

Bad: "This could potentially possibly improve performance in some cases."
Better: "This may improve performance." or "In our tests, this improved performance by 12%."

### Vague attribution

| Avoid | Use instead |
|---|---|
| "Experts believe" | (Name the experts or cite the source.) |
| "Studies show" | (Which studies? Link or cite.) |
| "Industry reports indicate" | (Which report? Be specific.) |
| "Some critics argue" | (Who? If it matters, name them.) |

---

## Structural Patterns

### Rule of three

AI defaults to three items in every list, three adjectives in every description, three examples in every illustration. This creates an unnatural rhythm. Use the number of items the content actually requires - sometimes that's two, sometimes five, sometimes one.

**AI pattern:** "The platform is fast, reliable, and scalable."
**Human alternative:** "The platform is fast and reliable." (if scalability isn't the point) or "The platform handles 10k requests/second with 99.9% uptime." (if specifics matter more)

### Negative parallelism

"It's not X, it's Y" / "Not only X but Y" - AI uses this as a primary rhetorical device. Humans use it occasionally for emphasis. If this construction appears more than once in a document, it's too many.

### False range

"From X to Y" constructions that don't describe an actual spectrum.

**AI pattern:** "From bustling cities to serene landscapes"
**Why it fails:** This isn't a range. It's two unrelated things joined by a false construction.

### Participial phrase padding

Main clause + comma + "-ing" phrase used to add hollow commentary.

**AI pattern:** "The team shipped the new indexer, showcasing their commitment to performance."
**Human alternative:** "The team shipped the new indexer." (The commitment is implied by the action.)

Common padding participles to watch for: ensuring, highlighting, emphasizing, reflecting, showcasing, demonstrating, underscoring, illustrating.

### Copula avoidance

Using "serves as," "functions as," "acts as" instead of "is."

**AI pattern:** "Redis serves as the caching layer."
**Human alternative:** "Redis is the caching layer."

### Synonym cycling

Referring to the same thing by different names in consecutive sentences to avoid repetition.

**AI pattern:** "The platform handles auth. The solution also manages sessions. The system provides SSO."
**Human alternative:** "The platform handles auth, manages sessions, and provides SSO."

Repeating the same noun is fine. Readers don't notice consistent naming. They do notice forced synonym swaps.

### Formulaic paragraph structure

AI paragraphs often follow: topic sentence, supporting detail, summary/transition. This creates a textbook rhythm that real writing doesn't have. Mix it up - start some paragraphs with evidence, some with a question, some with a blunt statement. Let the content determine the shape.

---

## Formatting Tells

### Em dashes and double hyphens

Never use em dashes (`—`) or double hyphens (`--`). Both are AI tells. No human writes with double hyphens, and em dashes are massively overused by AI models. Use commas, a single hyphen with spaces (` - `), parentheses, colons, or restructure into separate sentences.

### Bold-colon pattern

**AI pattern:**
> **Performance:** The system processes 1,000 requests per second.
> **Reliability:** Uptime exceeds 99.9%.

This structure is fine in genuinely tabular content (changelogs, spec sheets). In running prose, weave the information into paragraphs.

### Excessive use of lists

Not everything is a list. AI defaults to bullet points because they're structurally safe - each point is independent, reducing the chance of incoherence. But professional writing uses prose paragraphs as the default, with lists reserved for genuinely parallel, scannable content.

### Markdown artifacts in context

Headers, bold text, and bullet points should be used because they serve the reader, not because they fill space. A two-paragraph explanation doesn't need three subheadings.

### Emoji

Never in professional artifacts. No exceptions.
