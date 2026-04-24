# Excalidraw Diagram Skill

A skill that turns text descriptions into styled architecture diagrams. You describe the system; the skill writes a semantic model, runs graphviz for layout, and emits a valid `.excalidraw` file. For sequence diagrams, flowcharts, class diagrams, state diagrams, ERDs, and DFDs, it writes Mermaid source and converts that instead.

The output looks hand-placed but every coordinate comes from graphviz `dot` with orthogonal routing. No manual positioning, no arrow crossings, no guesswork.

## What it produces

Architecture diagrams from a plain-English description of your system. The skill generates `.excalidraw` files with proper element bindings, consistent colour semantics, zero roughness, and evidence artifacts for technical diagrams. Mermaid-lane diagrams go through the official Excalidraw converter via Playwright.

## Install

You need `graphviz` (for layout), `uv` (for the Python venv), and Playwright's Chromium binary (for rendering and Mermaid conversion). Total disk footprint is about 205 MB.

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

Verify the install:

```bash
dot -V                                 # graphviz 2.42+
uv run python -c "import playwright"   # silent on success
```

## Quick start

Ask your agent to create an architecture diagram for any system. The skill will read its feedback log, classify the diagram type, build a semantic model, run the layout script, render a PNG for visual inspection, and deliver the `.excalidraw` file.

The semantic model is a JSON file with nodes, edges, sections, and evidence artifacts. You describe what the system does; the agent fills in the model; graphviz computes every coordinate.

## Customise the look

All visual choices live in `theme.json` at the skill root: colour palette, font family, font sizes, corner radius, canvas background. Edit it to reskin every diagram.

The layout script also accepts `--theme <path>` and the `EXCALIDRAW_THEME` env var for one-off overrides.

To change the service colour from blue to corporate navy, edit `theme.json`:

```json
"service": { "stroke": "#0b5394", "fill": "#cfe2f3" }
```

See `references/theming.md` for every key explained, plus three drop-in palette examples (corporate blue, dark mode, hand-drawn casual).

## How it works

The agent writes a semantic model JSON (nodes, edges, sections). The layout script feeds that to graphviz `dot` with `splines=ortho`, maps the positions into Excalidraw elements with full bindings and theme colours, and writes the `.excalidraw` file. Playwright renders a PNG so the agent can inspect for overlaps, missing labels, or off-canvas nodes. If something looks wrong, the agent revises the model and re-runs (up to two passes).

## Feedback loop

When you rate a diagram and say what would improve it, the agent updates the relevant reference file immediately in the same session. `references/corrections.md` logs every correction so the change history is visible.

## Run evals

```bash
uv run python scripts/run_evals.py --workspace /tmp/excalidraw-ws-N
```

## Validate after edits

```bash
uv run python scripts/validate_skill.py --skill .
```

## Run the tests

```bash
for f in scripts/tests/*.test.py; do uv run python "$f" || break; done
```

## Credits

[coleam00/excalidraw-diagram-skill](https://github.com/coleam00/excalidraw-diagram-skill).
