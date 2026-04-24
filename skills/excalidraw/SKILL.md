---
name: excalidraw
description: Use when creating, editing, or reviewing .excalidraw / .excalidraw.json files, or when the user asks for an architecture diagram, sequence diagram, flowchart, class diagram, state diagram, ERD, data flow diagram, or any system-design visualisation for documentation. The agent composes Excalidraw JSON via the bundled Python layout script and renders-and-refines via the bundled Playwright render script before delivering.
allowed-tools: Read Write Edit Bash Glob Grep
---

## The iron rule

The main agent never reads `.excalidraw` JSON directly. File I/O, JSON composition, and rendering are delegated to subagents. The main agent sees only semantic summaries and screenshots.

## Five non-negotiable defaults

These apply to every element in every diagram. Do not look them up. They are here:

1. `fontFamily` matches `theme.json` typography (default `2` Helvetica). Evidence artifact text always uses `3` (monospace).
2. `roughness: 0` on every element, no exceptions.
3. Labels live inside shapes via `containerId` binding, not as floating text. The bound text element needs `strokeColor` from `theme.colors.text.stroke` (never `"transparent"`) and `autoResize: true`.
4. Every arrow has `startBinding` and `endBinding` set to real element IDs. Every arrow has a label unless the relationship is visually unambiguous from context.
5. No arrow crossings. If the graph layout forces crossings, restructure the layout before emitting JSON.

## Workflow

For every diagram request, follow these steps in order.

**Step 1 — Load past feedback.**
Read `references/corrections.md`. This is mandatory before any generation.

**Step 2 — Identify type.**
Match the request to a diagram type: architecture, flowchart, sequence, class, state, ERD, DFD, or other. All types go through the same pipeline.

**Step 2b — Depth assessment.**
Classify the request as conceptual (explaining a pattern) or technical (documentation for people running the system). This changes labelling, scope, and whether to include evidence artifacts (real event names, endpoints, payload shapes). See `references/design-principles.md` § "The diagram should argue, not display" for the full contrast table. If the request is ambiguous, ask the user.

---

### Steps 3a–3g: Build, layout, render

**Step 3a.** Read `references/design-principles.md`.

**Step 3b.** Read `references/diagram-patterns.md` — only the H2 section matching the diagram type.

**Step 3c.** Read `references/layout-formulas.md`.

**Step 3d — Build the semantic model as JSON.** Before touching any file, write a model file matching the shape the layout script expects:

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

For non-architecture types, map them into this model:
- **Flowchart**: use `kind: "decision"` for branch points, `kind: "service"` for process steps, `kind: "external"` for start/end terminals. Use `style: "dashed"` for feedback/retry edges.
- **Sequence**: model each actor as a node, each message as an edge. Use `direction: "LR"` with sections to group by phase. Number messages in edge labels.
- **Class**: model each class as a node. Use evidence artifacts anchored to each node for properties/methods. Relationships become edges.
- **State/ERD/DFD**: nodes are states/entities/processes, edges are transitions/relationships/data flows.

**Step 3e — Run the layout script.** From the skill root:

```
uv run python scripts/layout_architecture.py --input <model.json> --output <target>.excalidraw --seed 1
```

The script calls graphviz `dot` with `splines=ortho` and emits a fully styled `.excalidraw` file: orthogonal arrow routing, section frames, evidence artifacts, title/subtitle, and every styling invariant from `theme.json`.

Fall back to hand-placed coordinates from `layout-formulas.md` only when:
- the diagram has five or fewer nodes, or
- `dot` is unavailable in the environment.

**Step 3f — Read `references/json-reference.md` only if you must hand-emit.** The script path skips this step.

**Step 3g — Render and inspect.** Dispatch the render-and-inspect subagent (see template below). When the screenshot comes back, open it yourself. Look at it as a reader would: can you read every word? Does the diagram make sense at a glance? If something looks wrong, it is wrong — do not rationalise it away because the JSON metrics looked fine.

**Step 3h.** If issues found: fix every one of them. Revise the semantic model (reposition evidence cards, adjust sections, rename labels, remove clutter), re-run layout (step 3e), re-render (step 3g). Repeat until the render is clean. Do not deliver a diagram with known issues. If after two revision passes issues remain that cannot be fixed from the model (layout script bugs, graphviz limitations), tell the user exactly what is wrong and why it cannot be fixed — do not silently ship broken output.

---

**Step 4.** Report the saved file path to the user.

**Step 5.** Prompt the user: "Rate this /10 and say what would take it higher. (Skip to commit as-is.)"

**Step 6 — Act on feedback immediately.**
- On any rating: append `{"date":"<ISO>","diagram_type":"<type>","rating":<N>,"skill_version":"2.0"}` to `references/rating-log.jsonl`.
- On rating with critique: update the relevant reference file right now (`design-principles.md`, `diagram-patterns.md`, `theme.json`, or the layout script). Then log the correction to `references/corrections.md` so the change is recorded.

## Reference file load triggers

| File | When to read |
|---|---|
| `references/corrections.md` | At the start of every generation, always |
| `references/design-principles.md` | At Step 2b for depth assessment; again in full at Step 3a |
| `references/diagram-patterns.md` | After picking the type — read only the matching H2 section |
| `references/layout-formulas.md` | At Step 3c |
| `references/json-reference.md` | Only when the hand-emission fallback path is used |
| `references/theming.md` | When the user asks to restyle or reskin diagrams |

## Delegation templates

### JSON emission subagent (hand-emit fallback)

```
Task: Write Excalidraw JSON for a diagram.
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

### Render-and-inspect subagent

```
Task: Render an Excalidraw file and judge whether a reader would
find the diagram clear and complete.

Run: uv run python scripts/render.py --input <target>.excalidraw --output <target>.png --width 2400 --height 1600

Then open the PNG and evaluate it the way someone opening this
diagram for the first time would. You are not checking a list —
you are reading a diagram. Ask yourself:

  1. Can I read every word? Is any text cut off, truncated,
     overlapping another element, or invisible?
  2. Does the layout make sense at a glance? Can I follow the
     flow without tracing arrows back and forth?
  3. Is anything confusing, cluttered, or missing?

If something looks wrong, it IS wrong — do not explain it away
because "the JSON looked fine." Visual output is the only truth.

Return { screenshotPath, issues: [...] } where each issue is a
plain sentence describing what a reader would see. If there are
no issues, say so. Do NOT return raw JSON from the file.
```
