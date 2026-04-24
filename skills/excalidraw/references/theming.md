# Theming

`theme.json` at the skill root controls every visual choice the layout script makes. Override the file in place to reskin every diagram the skill produces. The script falls back to the values shown below when the file is missing or malformed.

---

## Keys

### `typography`

| Key | What it sets | Default |
|---|---|---|
| `fontFamily` | Excalidraw font family integer used everywhere except evidence artifacts. `2` = Helvetica, `3` = Cascadia (sans), `5` = Excalifont, `1` = Virgil (hand-drawn). Evidence artifacts always use `3` (monospace) regardless of this setting. | `3` |
| `titleSize` | Diagram title px | `40` |
| `subtitleSize` | Subtitle px | `18` |
| `sectionHeaderSize` | Uppercase column-header px (LR diagrams) and section frame label | `18` |
| `bodySize` | Default node label px before auto-shrink | `16` |
| `arrowLabelSize` | Arrow midpoint label px and evidence artifact text px | `14` |

### `shapes`

| Key | What it sets | Default |
|---|---|---|
| `roundness` | Excalidraw `roundness` object. `null` for sharp corners, `{"type": 3}` for default rounded | `null` |
| `strokeWidth` | Stroke width on node rectangles | `2` |
| `frameStrokeWidth` | Stroke width on dashed section frames | `1` |
| `arrowStrokeWidth` | Stroke width on arrows | `2` |
| `roughness` | Hand-drawn jitter on every element. `0` = precise lines, `1` = sketch, `2` = whiteboard | `0` |
| `fillStyle` | How shape fills render. `"solid"`, `"hachure"`, or `"cross-hatch"` | `"solid"` |

### `colors`

A semantic-role map. The script reads `colors[kind].stroke` and `colors[kind].fill` for every node based on its `kind` field. Stable role names: `service`, `datastore`, `queue`, `external`, `ui`, `decision`, `ai`, `error`. Reskin any role by editing its hex pair.

Special roles:

- `evidence.background` and `evidence.stroke`: the dark-slate / green pair for evidence artifact rectangles. The bound text uses `evidence.stroke` as ink colour.
- `frame.stroke`: colour of dashed section frames and their labels.
- `text.stroke`: ink colour for every text element except evidence text and the subtitle (which is hardcoded to a softer grey).

### `canvas`

| Key | What it sets | Default |
|---|---|---|
| `backgroundColor` | Excalidraw `appState.viewBackgroundColor`. Set this to invert canvas to dark | `#ffffff` |

---

## Override examples

### Corporate blue

Darker palette, Helvetica, sharp corners. Drop into `theme.json`:

```json
{
  "typography": { "fontFamily": 2, "titleSize": 36, "subtitleSize": 16,
                  "sectionHeaderSize": 16, "bodySize": 16, "arrowLabelSize": 13 },
  "shapes": { "roundness": null, "strokeWidth": 2, "frameStrokeWidth": 1 },
  "colors": {
    "service":   { "stroke": "#0b5394", "fill": "#cfe2f3" },
    "datastore": { "stroke": "#351c75", "fill": "#d9d2e9" },
    "queue":     { "stroke": "#bf9000", "fill": "#fff2cc" },
    "external":  { "stroke": "#666666", "fill": "#cccccc" },
    "ui":        { "stroke": "#274e13", "fill": "#d9ead3" },
    "decision":  { "stroke": "#b45f06", "fill": "#fce5cd" },
    "ai":        { "stroke": "#5b3d99", "fill": "#d9d2e9" },
    "error":     { "stroke": "#990000", "fill": "#f4cccc" },
    "evidence":  { "background": "#0b1729", "stroke": "#22c55e" },
    "frame":     { "stroke": "#444444" },
    "text":      { "stroke": "#000000" }
  },
  "canvas": { "backgroundColor": "#ffffff" }
}
```

### Dark mode

Inverted canvas, lighter text, brighter accents.

```json
{
  "typography": { "fontFamily": 3, "titleSize": 40, "subtitleSize": 18,
                  "sectionHeaderSize": 18, "bodySize": 16, "arrowLabelSize": 14 },
  "shapes": { "roundness": { "type": 3 }, "strokeWidth": 2, "frameStrokeWidth": 1 },
  "colors": {
    "service":   { "stroke": "#60a5fa", "fill": "#1e3a8a" },
    "datastore": { "stroke": "#a78bfa", "fill": "#3b1d6e" },
    "queue":     { "stroke": "#fbbf24", "fill": "#5b3a06" },
    "external":  { "stroke": "#cbd5e1", "fill": "#334155" },
    "ui":        { "stroke": "#86efac", "fill": "#14532d" },
    "decision":  { "stroke": "#fb923c", "fill": "#7c2d12" },
    "ai":        { "stroke": "#c4b5fd", "fill": "#4c1d95" },
    "error":     { "stroke": "#fca5a5", "fill": "#7f1d1d" },
    "evidence":  { "background": "#020617", "stroke": "#4ade80" },
    "frame":     { "stroke": "#94a3b8" },
    "text":      { "stroke": "#f1f5f9" }
  },
  "canvas": { "backgroundColor": "#0f172a" }
}
```

### Hand-drawn casual

Excalifont, sketch roughness, hachure fills, thin strokes. Produces whiteboard output from the theme alone — no post-process pass needed.

```json
{
  "typography": { "fontFamily": 5, "titleSize": 38, "subtitleSize": 18,
                  "sectionHeaderSize": 18, "bodySize": 18, "arrowLabelSize": 16 },
  "shapes": { "roundness": null, "strokeWidth": 1, "frameStrokeWidth": 1,
              "arrowStrokeWidth": 1, "roughness": 1, "fillStyle": "hachure" },
  "colors": {
    "service":   { "stroke": "#1971c2", "fill": "#a5d8ff" },
    "datastore": { "stroke": "#6741d9", "fill": "#d0bfff" },
    "queue":     { "stroke": "#f08c00", "fill": "#ffec99" },
    "external":  { "stroke": "#868e96", "fill": "#dee2e6" },
    "ui":        { "stroke": "#2f9e44", "fill": "#b2f2bb" },
    "decision":  { "stroke": "#e8590c", "fill": "#ffd8a8" },
    "ai":        { "stroke": "#6d28d9", "fill": "#ddd6fe" },
    "error":     { "stroke": "#c92a2a", "fill": "#ffc9c9" },
    "evidence":  { "background": "#1e293b", "stroke": "#22c55e" },
    "frame":     { "stroke": "#495057" },
    "text":      { "stroke": "#1e1e1e" }
  },
  "canvas": { "backgroundColor": "#fdf6e3" }
}
```

---

## Constraints worth keeping

The 60-30-10 rule, "stroke darker than fill", and the 4-accent cap all still apply. A theme that picks four neon colours will not magically produce a clean diagram. The semantic roles are stable; their hex values are not. Pick palettes that respect the rules in `design-principles.md`.
