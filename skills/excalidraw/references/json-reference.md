# JSON Reference

Copy-paste snippets for every Excalidraw element type. This file exists for the hand-emit fallback path only. The layout script handles JSON emission for the primary path.

Every required field is shown. Do not invent fields that are not listed here; do not omit fields that are shown.

For colour codes and arrow semantics, see `references/design-principles.md`. For coordinate arithmetic, see `references/layout-formulas.md`.

---

## Top-level file shape

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "excalidraw-skill",
  "elements": [],
  "appState": {
    "gridSize": null,
    "viewBackgroundColor": "#ffffff"
  },
  "files": {}
}
```

---

## Common fields on every element

| Field | Type | Default / Notes |
|-------|------|-----------------|
| `id` | string | Unique per file. Use a short random-looking string, e.g. `"svc-auth-01"`. |
| `angle` | number | `0` |
| `strokeColor` | string | Hex code from the semantic colour map. |
| `backgroundColor` | string | Hex fill, or `"transparent"` for arrows and text elements. |
| `fillStyle` | string | `"solid"` |
| `strokeWidth` | number | `2` for shapes and arrows; `1` for frame borders and lifelines. |
| `strokeStyle` | string | `"solid"` |
| `roughness` | number | `0` |
| `opacity` | number | `100` |
| `roundness` | null | Always `null` for technical diagrams. |
| `seed` | number | Any random integer. |
| `version` | number | `1` |
| `versionNonce` | number | Any random integer. |
| `isDeleted` | boolean | `false` |
| `groupIds` | array | `[]` |
| `frameId` | null | `null` |
| `boundElements` | array | References to child text or connected arrows (see each type below). |
| `updated` | number | Unix millisecond timestamp, e.g. `1700000000000`. |
| `link` | null | `null` |
| `locked` | boolean | `false` |
| `index` | string | Lexicographic z-order string. Use zero-padded values: `"a00"`, `"a01"`, `"a02"`, ... in emission order. See the ordering section below. |

---

## Rectangle (service / datastore / queue / ui)

```json
{
  "id": "svc-auth",
  "type": "rectangle",
  "x": 100, "y": 460, "width": 180, "height": 80,
  "strokeColor": "#1971c2", "backgroundColor": "#a5d8ff",
  "boundElements": [
    { "id": "txt-svc-auth", "type": "text" },
    { "id": "arr-gw-to-auth", "type": "arrow" }
  ],
  "index": "a04"
}
```

`boundElements` lists one `"type": "text"` entry for the label, plus one `"type": "arrow"` entry per attached arrow.

All common fields from the table above apply and must be included in the actual output.

---

## Text (bound label inside a shape)

Critical quirks:
- `strokeColor` controls ink colour. Setting it to `"transparent"` makes the label invisible.
- `containerId` must point to the parent rectangle's `id`.
- `autoResize: true` is required. Without it, container-bound text does not reflow.
- `backgroundColor: "transparent"` always.

```json
{
  "id": "txt-svc-auth",
  "type": "text",
  "x": 124, "y": 487.5, "width": 132, "height": 25,
  "strokeColor": "#1e1e1e", "backgroundColor": "transparent",
  "text": "Auth service", "originalText": "Auth service",
  "fontSize": 20, "fontFamily": 2,
  "textAlign": "center", "verticalAlign": "middle",
  "baseline": 18, "containerId": "svc-auth",
  "lineHeight": 1.25, "autoResize": true,
  "index": "a05"
}
```

### Positioning the text inside its container

```
text.x = container.x + (container.width  - text.width)  / 2
text.y = container.y + (container.height - text.height) / 2
```

Estimate `text.width` as `label_chars * fontSize * 0.6`. Estimate `text.height` as `fontSize * lineHeight`.

### Font sizes

| Context | fontSize |
|---------|---------|
| Box label | 20 |
| Arrow label | 16 |
| Frame label | 16 |
| Annotation / note | 14 |

Set `baseline` to approximately `fontSize * 0.9`: `18` for fontSize 20, `14` for fontSize 16.

Always `fontFamily: 2` (Helvetica). Never mix font families within a diagram.

---

## Text (free-floating, e.g. arrow label)

Arrow labels are free-floating text elements. Key differences from bound text: `containerId: null`, `strokeWidth: 1`, `fontSize: 16`. Position comes from the arrow midpoint formula in `references/layout-formulas.md`.

Free-floating text does not appear in any rectangle's `boundElements` array.

---

## Arrow

Every arrow requires both `startBinding` and `endBinding`.

```json
{
  "id": "arr-gw-to-auth",
  "type": "arrow",
  "x": 416, "y": 280, "width": 197, "height": 100,
  "strokeColor": "#1e1e1e", "backgroundColor": "transparent",
  "points": [[0, 0], [-197, 100]],
  "lastCommittedPoint": null,
  "startBinding": { "elementId": "gw-01", "focus": 0, "gap": 4 },
  "endBinding": { "elementId": "svc-auth", "focus": 0, "gap": 4 },
  "startArrowhead": null, "endArrowhead": "arrow",
  "index": "a15"
}
```

### Key arrow fields

- `x`, `y`: absolute coordinate of the start point.
- `points`: array of `[dx, dy]` pairs relative to `[x, y]`. First point is always `[0, 0]`. Last point is `[end_x - start_x, end_y - start_y]`.
- `width`: `Math.abs(last_point[0])`.
- `height`: `Math.abs(last_point[1])`.
- `focus: 0` in bindings centres the attachment on the bound shape's edge.
- `gap: 4` creates a 4px standoff between arrowhead and shape border.

Arrow `strokeColor` is always `"#1e1e1e"`. Use line style for semantic meaning, not colour.

### Arrow styles

| Meaning | strokeStyle | endArrowhead |
|---------|-------------|--------------|
| Primary flow / sync request | `"solid"` | `"arrow"` |
| Response / async / callback | `"dashed"` | `"arrow"` |
| Optional / feature-flag path | `"dotted"` | `"arrow"` |
| Association (no direction) | `"solid"` | `null` |

---

## Frame (swimlane / layer group)

Use a plain dashed rectangle, not Excalidraw's native `"frame"` type. The native frame clips children and shows a header tab; the dashed rectangle gives grouping without those side effects.

```json
{
  "id": "frame-presentation",
  "type": "rectangle",
  "x": 220, "y": 100, "width": 540, "height": 140,
  "strokeColor": "#495057", "backgroundColor": "transparent",
  "strokeStyle": "dashed", "strokeWidth": 1,
  "boundElements": [{ "id": "txt-frame-presentation", "type": "text" }],
  "index": "a00"
}
```

Label position: `x = frame.x + 12`, `y = frame.y + 4`. This places the label inside the frame border at the top-left, with ~26px clearance before the first node (nodes start at `frame.y + 30`).

---

## Element ordering (`index` field)

Excalidraw renders elements in ascending lexicographic order of `index`. Elements with lower indices render behind those with higher indices.

Assignment rule: frames first, then shape rectangles, then arrows, then text labels on top.

### WARNING: `"a10"` sorts BEFORE `"a2"`

Lexicographic comparison means `"a10"` < `"a2"` because `"1"` < `"2"` at the second character. Excalidraw validates index ordering at load time and silently rejects out-of-order files.

Zero-pad the numeric suffix to the digit-count of your element total:

```
Up to 100 elements: "a00", "a01", ..., "a09", "a10", ..., "a99"
Up to 1000 elements: "a000", "a001", ..., "a099", "a100", ..., "a999"
```

To insert between two existing indices, append an uppercase letter: between `"a00"` and `"a01"`, use `"a00V"`.
