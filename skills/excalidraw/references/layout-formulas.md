# Layout Formulas

Concrete arithmetic for placing elements. Apply these before emitting any JSON. Positions are computed, not guessed.

Read `references/design-principles.md` for colour rules, arrow semantics, and shape conventions. This file covers only coordinates and sizing.

---

## Canvas and origin

Start every diagram with a 100px margin at the top-left corner. All coordinates are absolute canvas coordinates, and the first element goes no earlier than `x=100, y=100`.

Target canvas width: 1200-1600px. Height grows downward as needed. Keep all elements in the top-left quadrant (positive x, positive y) so Excalidraw's fit-to-viewport centres the diagram correctly.

Do not place elements beyond x=2000 or y=2000. A diagram that needs more space is too large for one canvas.

---

## Node sizing by kind

| Kind | Width | Height |
|------|-------|--------|
| service | 180 | 80 |
| ui component | 180 | 80 |
| decision / diamond | 180 | 80 |
| datastore | 160 | 60 |
| queue / event stream | 200 | 80 |
| external system | 160 | 60 |
| frame / layer | computed (padding-based, see below) | computed |

---

## Grid math

```
col_width  = 300   # horizontal step between column origins
row_height = 180   # vertical step between row origins

node_x(col) = 100 + col * col_width
node_y(row) = 100 + row * row_height
```

Gap rules derived from the formulas above:

- Horizontal gap between edges of 180px-wide service nodes in adjacent columns: 300 - 180 = 120px.
- Vertical gap between edges of 80px-tall service nodes in adjacent rows: 180 - 80 = 100px.

For a diagram with N service columns, the total canvas width is approximately `100 + (N-1) * 300 + 180 + 100` (left margin + column span + node width + right margin).

---

## Arrow routing

### Straight arrow

Use when the source and target are roughly aligned vertically or horizontally.

```
# Vertical arrow (top to bottom):
start_x = source.x + source.width / 2
start_y = source.y + source.height          # bottom edge
end_x   = target.x + target.width / 2
end_y   = target.y                          # top edge

arrow.x      = start_x
arrow.y      = start_y
arrow.points = [[0, 0], [end_x - start_x, end_y - start_y]]
arrow.width  = |end_x - start_x|
arrow.height = |end_y - start_y|
```

```
# Horizontal arrow (left to right):
start_x = source.x + source.width          # right edge
start_y = source.y + source.height / 2
end_x   = target.x                         # left edge
end_y   = target.y + target.height / 2

arrow.x      = start_x
arrow.y      = start_y
arrow.points = [[0, 0], [end_x - start_x, end_y - start_y]]
```

With `startBinding` and `endBinding` set, Excalidraw snaps arrow endpoints to element edges at render time. The stored `points` should still use edge coordinates as above.

### Orthogonal (L-shaped) arrow

Use when a diagonal line would cross other elements.

```
mid_x = (start_x + end_x) / 2

arrow.points = [
  [0, 0],
  [mid_x - start_x, 0],                    # horizontal leg
  [mid_x - start_x, end_y - start_y]       # vertical leg to target
]
```

### Gap value in bindings

Use `"gap": 4` for direct connections (4px standoff prevents arrowhead/shape overlap). Use `"gap": 8` when the shape has a thick stroke (strokeWidth 3+).

---

## Arrow label placement

Arrow labels are free-floating text elements (containerId: null) positioned at the arrow's midpoint with a perpendicular offset.

```
# For a roughly horizontal arrow:
label_x = mid_x - estimated_label_width / 2
label_y = mid_y - 20                        # 20px above the arrow line

# For a roughly vertical arrow:
label_x = mid_x + 20                        # 20px right of the arrow line
label_y = mid_y - estimated_label_height / 2
```

Estimated label width: `string.length * fontSize * 0.6`. At fontSize 16, "place order" (11 chars) is about 106px wide.

When 3+ arrows converge on one node, offset each label 35px from the midpoint along the arrow's direction so labels do not pile up. Adjacent labels should be at least 25 degrees apart.

---

## Subgraph frames

Frames wrap a group of nodes to show layering, swimlanes, or bounded contexts. They are plain rectangles with dashed strokes, not Excalidraw's native frame element type.

```
frame_x      = min(child.x) - padding
frame_y      = min(child.y) - padding
frame_width  = max(child.x + child.width)  - frame_x + padding
frame_height = max(child.y + child.height) - frame_y + padding

padding = 30
```

Frame label position:

```
label_x = frame_x + 12
label_y = frame_y + 4
```

Frame JSON fields:

```json
{
  "strokeColor": "#495057",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeStyle": "dashed",
  "strokeWidth": 1,
  "roughness": 0
}
```

---

## Validation checklist

Run this mentally before emitting the final JSON:

1. No two node bounding boxes overlap. For every pair (A, B): `A.x + A.width <= B.x` or `B.x + B.width <= A.x` or `A.y + A.height <= B.y` or `B.y + B.height <= A.y`.
2. No arrow path passes through a rectangle that is not the arrow's source or target.
3. Every arrow has both `startBinding.elementId` and `endBinding.elementId` pointing to real element IDs.
4. Every rectangle has exactly one text element whose `containerId` references that rectangle's `id`.
5. Canvas extent stays within 2000x2000px.
6. No more than 3 accent colour families (4 allowed when all four of UI/external, service, datastore, queue are present).

---

## Large-diagram strategy (12+ nodes)

When the semantic model has more than 12 nodes, switch from single-pass to two-pass construction with a three-zoom-level design constraint.

### The three zoom levels

Every large diagram must work at three levels of zoom:

1. **Overview.** Section labels readable. Individual nodes may not be.
2. **Section.** Every node in that section is readable. Cross-section arrows visible.
3. **Node.** Arrow labels readable for a single node and its neighbours.

This forces spatial discipline: section labels at 24+ px, internal labels at 20 px, arrow labels at 16 px. Section spacing must be at least 80 px.

### Two-pass construction

**Pass 1 -- Sections in isolation.** For each section, emit all its internal nodes, internal arrows, and a frame. Use descriptive IDs: `section-<name>-<node-kind>-<n>`. Only create internal arrows.

**Pass 2 -- Cross-section arrows.** Add arrows that cross section boundaries. Their bindings reference IDs from pass 1. Update `boundElements` on source and target nodes. Pass 2 never creates new nodes.

### Section placement on the canvas

```
section_x(col) = 100 + col * 600
section_y(row) = 100 + row * 400
```

For most architectures a linear arrangement or a 2xN grid works.

### When to cap

If the semantic model exceeds 25 nodes, stop. Ask the user whether to split the diagram into multiple files or drop detail. A 30-node single diagram is usually a failure to abstract, not a legitimate need.
