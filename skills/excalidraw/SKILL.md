---
name: excalidraw
description: Use when creating, editing, or reviewing .excalidraw / .excalidraw.json files, or when the user asks for an architecture diagram, sequence diagram, flowchart, class diagram, state diagram, ERD, data flow diagram, or any system-design visualisation for documentation. The agent composes Excalidraw JSON via the bundled Python layout script and renders-and-refines via the bundled Playwright render script before delivering.
allowed-tools: Read Write Edit Bash Glob Grep
---

## The iron rule

The main agent never reads `.excalidraw` JSON directly. File I/O, JSON composition, and rendering are delegated to subagents. The main agent sees only semantic summaries and screenshots.

## Five non-negotiable defaults

These apply to every element in every Create-lane diagram. Do not look them up. They are here:

1. `fontFamily` matches `theme.json` typography (default `2` Helvetica). Evidence artifact text always uses `3` (monospace).
2. `roughness: 0` on every element, no exceptions.
3. Labels live inside shapes via `containerId` binding, not as floating text. The bound text element needs `strokeColor` from `theme.colors.text.stroke` (never `"transparent"`) and `autoResize: true`.
4. Every arrow has `startBinding` and `endBinding` set to real element IDs. Every arrow has a label unless the relationship is visually unambiguous from context.
5. No arrow crossings. If the graph layout forces crossings, restructure the layout before emitting JSON.

## Two lanes

| Diagram type | Lane | Output |
|---|---|---|
| flowchart, sequence, class, state, ERD, DFD | Mermaid | `<name>.mmd` then converted to `.excalidraw` via the bundled script |
| architecture (microservices, layered, event-driven, hub-and-spoke, any novel topology) | Create | `.excalidraw` file written from scratch via layout script |

## Workflow

For every diagram request, follow these steps in order.

**Step 1 — Load past feedback.**
Read `references/corrections.md`. This is mandatory before any generation.

**Step 2 — Identify type and pick lane.**
Match the request to one of the diagram types above. Note the lane.

**Step 2b — Depth assessment.**
Classify the request as conceptual (explaining a pattern) or technical (documentation for people running the system). This changes labelling, scope, and whether to include evidence artifacts (real event names, endpoints, payload shapes). See `references/design-principles.md` § "The diagram should argue, not display" for the full contrast table. If the request is ambiguous, ask the user.

---

### Mermaid lane (steps 3a–3e)

**Step 3a.** Read `references/mermaid-lane.md`.

**Step 3b.** Read `references/diagram-patterns.md` — only the H2 section matching the diagram type.

**Step 3c.** Write the Mermaid source to `<target>.mmd`.

**Step 3d.** Dispatch a subagent: `uv run python scripts/mermaid_to_excalidraw.py --input <target>.mmd --output <target>.excalidraw`. The subagent returns `{ok, output, elements}`.

**Step 3e.** Continue to Step 5 (visual inspect via `scripts/render.py`).

---

### Create lane (steps 4a–4i)

**Step 4a.** Read `references/design-principles.md`.

**Step 4b.** Read `references/diagram-patterns.md` — only the Architecture H2 section.

**Step 4c.** Read `references/layout-formulas.md`.

**Step 4d — Build the semantic model as JSON.** Before touching any file, write a model file matching the shape the layout script expects:

```json
{
  "title": "One-line argument the diagram makes",
  "subtitle": "optional context line",
  "direction": "TB" | "LR",
  "nodes": [
    {"id": "...", "label": "...", "kind": "service|datastore|queue|external|ui|decision|ai", "section": "<sectionId or omit>"}
  ],
  "edges": [
    {"from": "...", "to": "...", "label": "...", "style": "solid|dashed|dotted"}
  ],
  "sections": [{"id": "...", "label": "..."}],
  "evidence": [
    {"anchor_near": "<nodeId>", "text": "topic: orders.v2\\npartitions: 16", "position": "right|left|above|below"}
  ]
}
```

This model captures every piece of information a reader needs. Do NOT hand-compute coordinates. That is the layout script's job.

**Step 4e — Run the layout script.** From the skill root:

```
uv run python scripts/layout_architecture.py --input <model.json> --output <target>.excalidraw --seed 1
```

The script calls graphviz `dot` (system prerequisite) with `splines=ortho` and emits a fully styled `.excalidraw` file: non-crossing orthogonal arrow routing, dashed section frames with labels, uppercase column headers for LR diagrams with sections, evidence-artifact rectangles at the anchors you listed, diagram title + subtitle, zero-padded indices, and every styling invariant. All visual choices come from `theme.json` at the skill root. See `references/theming.md` to override.

Fall back to hand-placed coordinates from `layout-formulas.md` only when:
- the diagram has five or fewer nodes (where the script is overkill), or
- `dot` is unavailable in the environment.

**Step 4f — Read `references/json-reference.md` only if you must hand-emit.** The script path skips this step.

**Step 4g — Subagent emission (fallback only).** For hand-placed fallback, dispatch the JSON-emission subagent. See template below.

**Step 4h — Render and inspect.** Dispatch a subagent: `uv run python scripts/render.py --input <target>.excalidraw --output <target>.png`. Examine the PNG for overlaps, crossings, missing labels, off-canvas nodes.

**Step 4i.** If issues are reported: revise the semantic model (add a section, flip edge direction, reroute through a relay node), re-emit (step 4e), re-render (step 4h). Maximum two refinement passes. If issues persist after two passes, report them to the user rather than silently delivering a broken diagram.

---

**Step 5 — Visual inspect (both lanes).** Dispatch the render subagent for the resulting `.excalidraw` file. Open the screenshot yourself and confirm no overlaps, no missing labels, no arrow crossings, no off-canvas nodes.

**Step 6.** Report the saved file path to the user.

**Step 7.** Prompt the user: "Rate this /10 and say what would take it higher. (Skip to commit as-is.)"

**Step 8 — Act on feedback immediately.**
- On any rating: append `{"date":"<ISO>","diagram_type":"<type>","rating":<N>,"skill_version":"2.0"}` to `references/rating-log.jsonl`.
- On rating with critique: update the relevant reference file right now (`design-principles.md`, `diagram-patterns.md`, `theme.json`, or the layout script). Then log the correction to `references/corrections.md` so the change is recorded.

## Reference file load triggers

| File | When to read |
|---|---|
| `references/corrections.md` | At the start of every generation, always |
| `references/design-principles.md` | At Step 2b for the depth-assessment section; again in full at Step 4a for the Create lane |
| `references/diagram-patterns.md` | After picking the type — read only the matching H2 section |
| `references/mermaid-lane.md` | Only when the Mermaid lane is chosen |
| `references/layout-formulas.md` | Only when the Create lane is chosen |
| `references/json-reference.md` | Only when the hand-emission fallback path is used |
| `references/theming.md` | When the user asks to restyle or reskin diagrams |

## Delegation templates

### Create-lane JSON emission subagent (hand-emit fallback)

```
Task: Write Excalidraw JSON for an architecture diagram.
Input: semantic model (nodes[], edges[], frames[])
Constraints: follow conventions from references/json-reference.md
and references/design-principles.md. Read theme.json from the skill
root for the colour map and typography.
  - roughness: 0 on every element
  - fontFamily from theme.typography.fontFamily on every text
    (evidence text uses 3)
  - every text element: strokeColor from theme.colors.text.stroke,
    autoResize true, containerId bound to parent shape
  - every arrow: startBinding and endBinding set to real element IDs
  - index field present on every element (zero-padded "a00", "a01", ...)
Output: write file at <path>, return {elements: N, bytes: M, path: "<path>"}.
```

### Mermaid lane subagent

```
Task: Convert <target>.mmd to <target>.excalidraw.
Run: uv run python scripts/mermaid_to_excalidraw.py --input <target>.mmd --output <target>.excalidraw
Return the JSON line on stdout: {ok, output, elements}.
```

### Render-and-inspect subagent

```
Task: Render an Excalidraw file and return a visual assessment.
Run: uv run python scripts/render.py --input <target>.excalidraw --output <target>.png --width 2400 --height 1600
Then open the PNG, look for: overlap | missing-label | arrow-crossing | off-canvas | other.
Return { screenshotPath, issues: [...] }. Do NOT return raw JSON.
```
