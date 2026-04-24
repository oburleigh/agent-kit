# Excalidraw Diagram Skill

Generates `.excalidraw` files from text descriptions. Handles architecture, flowcharts, sequence, class, state, ERD, and DFD diagrams. Layout comes from graphviz `dot` (orthogonal routing, no crossings), styling comes from `theme.json`, and every output is rendered to PNG so the agent can see what the reader will see before delivery.

## Install

Three dependencies: `graphviz` for layout, `uv` for the Python environment, Playwright's Chromium binary for rendering. Total footprint ~205 MB.

### macOS

```bash
brew install graphviz
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Debian / Ubuntu

```bash
sudo apt install graphviz
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Finish setup (both platforms)

```bash
cd <skill-install-path>/excalidraw
uv sync
uv run playwright install chromium
```

Verify:

```bash
dot -V                                 # graphviz 2.42+
uv run python -c "import playwright"   # silent on success
```

## Using the skill

Ask the agent to create a diagram. It will:

1. Read `references/corrections.md` to pick up prior feedback.
2. Classify the request — diagram type, and conceptual vs technical depth.
3. Write a semantic model: `nodes`, `edges`, optional `sections` and `evidence` artifacts.
4. Run `scripts/layout_architecture.py` to compute coordinates via graphviz and emit the `.excalidraw` file.
5. Render the file to PNG with `scripts/render.py` and inspect the image.
6. Revise the model and repeat until the render reads cleanly.
7. Deliver the `.excalidraw` path and invite a rating.

The agent never hand-edits coordinates. If the layout looks wrong, the fix happens in the semantic model, not the JSON.

## Styling

All visual choices route through `theme.json` at the skill root. Edit it to reskin every diagram the skill produces.

### What `theme.json` controls

| Section | Controls |
|---|---|
| `typography` | Font family (`1` Virgil, `2` Helvetica, `3` Cascadia, `5` Excalifont). Sizes for title, subtitle, section headers, body, arrow labels. |
| `shapes.strokeWidth` | Stroke width on node shapes. |
| `shapes.frameStrokeWidth` | Stroke width on section frames. |
| `shapes.arrowStrokeWidth` | Stroke width on arrows. |
| `shapes.roundness` | Corner style. `null` for sharp, `{"type": 3}` for rounded. |
| `shapes.roughness` | Hand-drawn jitter. `0` precise, `1` sketch, `2` whiteboard. |
| `shapes.fillStyle` | Shape fill treatment. `"solid"`, `"hachure"`, or `"cross-hatch"`. |
| `colors` | Per-role palette: `service`, `datastore`, `queue`, `external`, `ui`, `decision`, `ai`, `error`, plus special roles `evidence`, `frame`, `text`. Each role has a `stroke` / `fill` hex pair. |
| `canvas.backgroundColor` | Excalidraw canvas background. Flip to a dark hex for dark-mode output. |

Every visual token the output depends on is in this file. Change corporate blue to whiteboard sketch to dark-mode neon by editing `theme.json` alone — no post-process step, no script edit. `references/theming.md` has three drop-in example themes (corporate blue, dark mode, hand-drawn casual) and notes on the constraints a custom palette should respect.

### One-off theme without editing the default

Every invocation of the layout script accepts an override path:

```bash
uv run python scripts/layout_architecture.py \
  --input model.json \
  --output diagram.excalidraw \
  --theme /path/to/custom-theme.json
```

Keep multiple theme files side by side and pass whichever matches the audience.

## Repository layout

```
README.md                  this file
SKILL.md                   agent-facing workflow spec
theme.json                 default visual tokens
pyproject.toml, uv.lock    Python env
references/
  corrections.md           feedback log, read at the start of every run
  design-principles.md     colour, spacing, typography, arrow semantics
  diagram-patterns.md      per-type conventions (architecture, sequence, ...)
  layout-formulas.md       coordinate arithmetic and validation checklist
  json-reference.md        Excalidraw JSON element fields
  theming.md               theme.json keys and palette examples
  rating-log.jsonl         append-only rating history
scripts/
  layout_architecture.py   semantic model -> .excalidraw (graphviz dot layout)
  render.py                .excalidraw -> PNG via Playwright
  validate_skill.py        structural checks over the skill tree
  tests/                   unit tests for the layout script
evals/                     skill-creator eval definitions
handoffs/                  design / decision notes from skill authors
```

## Validate and test

```bash
uv run python scripts/validate_skill.py --skill .
for f in scripts/tests/*.test.py; do uv run python "$f" || break; done
```

Evals are defined in `evals/evals.json` and run via `/skill-creator` in a Claude Code session.

## Credits

Based on [coleam00/excalidraw-diagram-skill](https://github.com/coleam00/excalidraw-diagram-skill).
