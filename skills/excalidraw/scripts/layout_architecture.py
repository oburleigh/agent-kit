#!/usr/bin/env python3
"""
layout_architecture.py

Graphviz-backed layout for Excalidraw architecture diagrams. Produces an
Excalidraw JSON file with non-crossing orthogonal arrow routing.

Input: a semantic-model JSON file matching the shape documented in
SKILL.md Step 4d. Output: a .excalidraw file written to --output.

Constraints:
  - stdlib only; shells out to `dot` (graphviz) via subprocess.
  - Preserves every one of Oli's styling rules: roughness 0, fontFamily 2
    (Helvetica) for body, fontFamily 3 (monospace) for evidence artifacts
    only, strokeColor "#1e1e1e" on text, autoResize true on bound text,
    containerId binding, zero-padded index, semantic colour map from
    references/design-principles.md, startBinding / endBinding on every
    arrow with gap 8, stroke darker than fill, strokeWidth 2 for shapes.

Usage:
    layout_architecture.py --input <graph.json> --output <diagram.excalidraw>
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


# ----------------------------------------------------------------------------
# Defaults — used when theme.json is missing or malformed.
# ----------------------------------------------------------------------------
_DEFAULT_THEME: dict[str, Any] = {
    "typography": {
        "fontFamily": 2,
        "titleSize": 36,
        "subtitleSize": 18,
        "sectionHeaderSize": 18,
        "bodySize": 16,
        "arrowLabelSize": 14,
    },
    "shapes": {
        "roundness": None,
        "strokeWidth": 2,
        "frameStrokeWidth": 1,
        "arrowStrokeWidth": 2,
        "roughness": 0,
        "fillStyle": "solid",
    },
    "colors": {
        "service":   {"stroke": "#1971c2", "fill": "#a5d8ff"},
        "datastore": {"stroke": "#6741d9", "fill": "#d0bfff"},
        "queue":     {"stroke": "#f08c00", "fill": "#ffec99"},
        "external":  {"stroke": "#868e96", "fill": "#dee2e6"},
        "ui":        {"stroke": "#2f9e44", "fill": "#b2f2bb"},
        "decision":  {"stroke": "#e8590c", "fill": "#ffd8a8"},
        "ai":        {"stroke": "#6d28d9", "fill": "#ddd6fe"},
        "error":     {"stroke": "#c92a2a", "fill": "#ffc9c9"},
        "evidence":  {"background": "#1e293b", "stroke": "#22c55e"},
        "frame":     {"stroke": "#495057"},
        "text":      {"stroke": "#1e1e1e"},
    },
    "canvas": {"backgroundColor": "#ffffff"},
}

# Theme path is the skill root (parent of scripts/).
_THEME_PATH = Path(__file__).resolve().parent.parent / "theme.json"


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_theme(path: Path | str | None = None) -> dict[str, Any]:
    """Load theme.json with fallback to baked-in defaults.

    Missing file or JSON parse errors emit a warning to stderr and return
    the defaults. Partial themes are merged on top of defaults.
    """
    p = Path(path) if path is not None else _THEME_PATH
    if not p.exists():
        return json.loads(json.dumps(_DEFAULT_THEME))
    try:
        with open(p, "r", encoding="utf-8") as f:
            user = json.load(f)
        if not isinstance(user, dict):
            raise ValueError("theme.json root must be an object")
        return _deep_merge(_DEFAULT_THEME, user)
    except (json.JSONDecodeError, ValueError, OSError) as e:
        print(f"warning: theme.json invalid ({e}); using defaults", file=sys.stderr)
        return json.loads(json.dumps(_DEFAULT_THEME))


# Load once at import time; tests can override by reassigning THEME or by
# calling load_theme(path) explicitly and rewiring helpers below.
THEME: dict[str, Any] = load_theme()


def _colors() -> dict[str, dict[str, str]]:
    return THEME.get("colors", _DEFAULT_THEME["colors"])


def _typography() -> dict[str, Any]:
    return THEME.get("typography", _DEFAULT_THEME["typography"])


def _shapes_cfg() -> dict[str, Any]:
    return THEME.get("shapes", _DEFAULT_THEME["shapes"])


# Aliases so existing call sites compile; values resolved at call time.
def _evidence_stroke() -> str:
    return _colors().get("evidence", {}).get("stroke", "#22c55e")


def _evidence_fill() -> str:
    return _colors().get("evidence", {}).get("background", "#1e293b")


def _text_ink() -> str:
    return _colors().get("text", {}).get("stroke", "#1e1e1e")


def _frame_stroke() -> str:
    return _colors().get("frame", {}).get("stroke", "#495057")


def _arrow_ink() -> str:
    # Arrows always use text-ink for consistency.
    return _text_ink()


# Backwards-compatible module constants (kept for any external import).
COLOURS = _DEFAULT_THEME["colors"]  # noqa: N816 — preserved name
EVIDENCE_STROKE = _DEFAULT_THEME["colors"]["evidence"]["stroke"]
EVIDENCE_FILL = _DEFAULT_THEME["colors"]["evidence"]["background"]
TEXT_INK = _DEFAULT_THEME["colors"]["text"]["stroke"]
ARROW_INK = _DEFAULT_THEME["colors"]["text"]["stroke"]

# Fixed node dims (inches for graphviz input; px 1:1 at dpi=72).
NODE_W_PX = 200
NODE_H_PX = 80
NODE_W_IN = NODE_W_PX / 72
NODE_H_IN = NODE_H_PX / 72

# Canvas padding so elements never touch (0,0); leaves room for title block.
CANVAS_PAD_X = 40
CANVAS_PAD_Y = 140  # title + subtitle + section column-header row


# ----------------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------------
def _rand_int() -> int:
    return random.randint(10_000_000, 99_999_999)


def _dot_escape(s: str) -> str:
    # Graphviz label syntax: escape backslash, quote, newline.
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _safe_id(s: str) -> str:
    # graphviz node ids must match [A-Za-z_][A-Za-z_0-9]* or be quoted.
    # We quote everything defensively.
    return '"' + _dot_escape(s) + '"'


def _pad(i: int, width: int) -> str:
    return f"a{i:0{width}d}"


def _estimate_text_width(text: str, font_size: int) -> float:
    # Rough Helvetica width heuristic. Matches json-reference.md: char * fs * 0.6.
    longest = max((len(line) for line in text.split("\n")), default=0)
    return longest * font_size * 0.6


def _text_height(text: str, font_size: int) -> float:
    lines = max(1, text.count("\n") + 1)
    return lines * font_size * 1.25


# ----------------------------------------------------------------------------
# Input validation
# ----------------------------------------------------------------------------
def validate_input(model: dict[str, Any]) -> None:
    if not isinstance(model, dict):
        raise ValueError("input must be a JSON object")
    if not isinstance(model.get("nodes"), list) or not model["nodes"]:
        raise ValueError("input.nodes must be a non-empty array")
    if not isinstance(model.get("edges"), list):
        raise ValueError("input.edges must be an array")
    seen_ids: set[str] = set()
    for i, n in enumerate(model["nodes"]):
        if not isinstance(n, dict) or not n.get("id") or not n.get("label"):
            raise ValueError(f"nodes[{i}] requires id and label")
        if n["id"] in seen_ids:
            raise ValueError(f"duplicate node id: {n['id']}")
        seen_ids.add(n["id"])
    for i, e in enumerate(model["edges"]):
        if not isinstance(e, dict) or not e.get("from") or not e.get("to"):
            raise ValueError(f"edges[{i}] requires from and to")
        if e["from"] not in seen_ids:
            raise ValueError(f"edges[{i}].from references unknown node {e['from']}")
        if e["to"] not in seen_ids:
            raise ValueError(f"edges[{i}].to references unknown node {e['to']}")
    direction = model.get("direction", "TB")
    if direction not in ("TB", "LR"):
        raise ValueError("direction must be TB or LR")


# ----------------------------------------------------------------------------
# DOT emission
# ----------------------------------------------------------------------------
def build_dot(model: dict[str, Any]) -> str:
    direction = model.get("direction", "TB")
    sections = model.get("sections", []) or []
    nodes = model["nodes"]
    edges = model["edges"]

    lines: list[str] = []
    lines.append("digraph G {")
    lines.append(f'  rankdir={direction};')
    lines.append("  splines=ortho;")
    lines.append("  nodesep=1.2;")
    lines.append("  ranksep=1.8;")
    lines.append("  compound=true;")
    lines.append('  graph [dpi=72, pad="0.5", margin="0.4"];')
    lines.append(
        f'  node [shape=box, fixedsize=true, width={NODE_W_IN:.4f}, '
        f"height={NODE_H_IN:.4f}];"
    )
    lines.append("  edge [arrowhead=normal];")

    # Partition nodes by section.
    by_section: dict[str, list[dict[str, Any]]] = {}
    unsectioned: list[dict[str, Any]] = []
    section_ids = {s["id"] for s in sections}
    for n in nodes:
        sid = n.get("section")
        if sid and sid in section_ids:
            by_section.setdefault(sid, []).append(n)
        else:
            unsectioned.append(n)

    # Emit clusters in the order given by `sections`.
    for section in sections:
        sid = section["id"]
        nodes_in = by_section.get(sid, [])
        if not nodes_in:
            continue
        # graphviz requires the subgraph name to start with "cluster".
        safe_sid = re.sub(r"[^A-Za-z0-9_]", "_", sid)
        lines.append(f"  subgraph cluster_{safe_sid} {{")
        lines.append(f'    label="{_dot_escape(section.get("label", sid))}";')
        lines.append('    style=dashed;')
        lines.append('    color="#495057";')
        lines.append('    fontname="Helvetica";')
        lines.append('    fontsize=16;')
        lines.append('    labeljust=l;')
        lines.append("    margin=24;")
        for n in nodes_in:
            lines.append(
                f'    {_safe_id(n["id"])} [label="{_dot_escape(n["label"])}"];'
            )
        lines.append("  }")

    # Unsectioned nodes at top level.
    for n in unsectioned:
        lines.append(f'  {_safe_id(n["id"])} [label="{_dot_escape(n["label"])}"];')

    # Edges.
    for e in edges:
        style_attr = ""
        style = e.get("style", "solid")
        if style == "dashed":
            style_attr = ' style=dashed'
        elif style == "dotted":
            style_attr = ' style=dotted'
        lbl = e.get("label")
        label_attr = f' label="{_dot_escape(lbl)}"' if lbl else ""
        lines.append(
            f"  {_safe_id(e['from'])} -> {_safe_id(e['to'])} "
            f"[{(label_attr + style_attr).strip()}];"
        )

    lines.append("}")
    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------------------
# Graphviz JSON parsing
# ----------------------------------------------------------------------------
def run_dot(dot_src: str) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["dot", "-Tjson", "-Gdpi=72"],
            input=dot_src,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as e:
        raise RuntimeError(
            "graphviz `dot` binary not found on PATH. "
            "Install with `apt install graphviz`."
        ) from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"dot failed (exit {e.returncode}): {e.stderr.strip()}"
        ) from e
    return json.loads(proc.stdout)


def _parse_bb(bb: str) -> tuple[float, float, float, float]:
    a, b, c, d = [float(x) for x in bb.split(",")]
    return a, b, c, d


def _flip_y(y: float, canvas_h: float) -> float:
    """Graphviz uses y-up, Excalidraw uses y-down. Flip around canvas_h."""
    return canvas_h - y


# ----------------------------------------------------------------------------
# Excalidraw element factories
# ----------------------------------------------------------------------------
def _base_element(
    *,
    el_id: str,
    el_type: str,
    x: float,
    y: float,
    width: float,
    height: float,
    stroke: str,
    fill: str,
    index: str,
    stroke_width: int = 2,
    stroke_style: str = "solid",
    bound: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    shapes_cfg = _shapes_cfg()
    return {
        "id": el_id,
        "type": el_type,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "angle": 0,
        "strokeColor": stroke,
        "backgroundColor": fill,
        "fillStyle": shapes_cfg.get("fillStyle", "solid"),
        "strokeWidth": stroke_width,
        "strokeStyle": stroke_style,
        "roughness": int(shapes_cfg.get("roughness", 0)),
        "opacity": 100,
        "roundness": shapes_cfg.get("roundness"),
        "seed": _rand_int(),
        "version": 1,
        "versionNonce": _rand_int(),
        "isDeleted": False,
        "groupIds": [],
        "frameId": None,
        "boundElements": bound or [],
        "updated": 1700000000000,
        "link": None,
        "locked": False,
        "index": index,
    }


def make_rect(
    el_id: str,
    x: float,
    y: float,
    w: float,
    h: float,
    stroke: str,
    fill: str,
    index: str,
    bound_text_id: str | None = None,
    stroke_width: int = 2,
    stroke_style: str = "solid",
) -> dict[str, Any]:
    bound: list[dict[str, str]] = []
    if bound_text_id:
        bound.append({"id": bound_text_id, "type": "text"})
    return _base_element(
        el_id=el_id,
        el_type="rectangle",
        x=x,
        y=y,
        width=w,
        height=h,
        stroke=stroke,
        fill=fill,
        index=index,
        stroke_width=stroke_width,
        stroke_style=stroke_style,
        bound=bound,
    )


def make_bound_text(
    el_id: str,
    container_id: str,
    container_x: float,
    container_y: float,
    container_w: float,
    container_h: float,
    text: str,
    font_size: int,
    index: str,
    font_family: int | None = None,
    stroke: str | None = None,
) -> dict[str, Any]:
    if font_family is None:
        font_family = int(_typography().get("fontFamily", 2))
    if stroke is None:
        stroke = _text_ink()
    w = _estimate_text_width(text, font_size)
    h = _text_height(text, font_size)
    # Centre inside container.
    x = container_x + (container_w - w) / 2
    y = container_y + (container_h - h) / 2
    baseline = int(round(font_size * 0.9))
    el = _base_element(
        el_id=el_id,
        el_type="text",
        x=x,
        y=y,
        width=w,
        height=h,
        stroke=stroke,
        fill="transparent",
        index=index,
    )
    el.update({
        "text": text,
        "originalText": text,
        "fontSize": font_size,
        "fontFamily": font_family,
        "textAlign": "center",
        "verticalAlign": "middle",
        "baseline": baseline,
        "containerId": container_id,
        "lineHeight": 1.25,
        "autoResize": True,
    })
    return el


def make_free_text(
    el_id: str,
    x: float,
    y: float,
    text: str,
    font_size: int,
    index: str,
    font_family: int | None = None,
    stroke: str | None = None,
    stroke_width: int = 1,
) -> dict[str, Any]:
    if font_family is None:
        font_family = int(_typography().get("fontFamily", 2))
    if stroke is None:
        stroke = _text_ink()
    w = _estimate_text_width(text, font_size)
    h = _text_height(text, font_size)
    baseline = int(round(font_size * 0.9))
    el = _base_element(
        el_id=el_id,
        el_type="text",
        x=x,
        y=y,
        width=w,
        height=h,
        stroke=stroke,
        fill="transparent",
        index=index,
        stroke_width=stroke_width,
    )
    el.update({
        "text": text,
        "originalText": text,
        "fontSize": font_size,
        "fontFamily": font_family,
        "textAlign": "left",
        "verticalAlign": "top",
        "baseline": baseline,
        "containerId": None,
        "lineHeight": 1.25,
        "autoResize": True,
    })
    return el


def make_arrow(
    el_id: str,
    start_id: str,
    end_id: str,
    points: list[list[float]],
    index: str,
    stroke_style: str = "solid",
    stroke_width: int = 2,
) -> dict[str, Any]:
    # points: absolute pixel coordinates; we rebase so points[0] = [0,0]
    # and el.x,el.y = first absolute point.
    ax, ay = points[0]
    rel = [[px - ax, py - ay] for px, py in points]
    w = max(abs(p[0]) for p in rel)
    h = max(abs(p[1]) for p in rel)
    el = _base_element(
        el_id=el_id,
        el_type="arrow",
        x=ax,
        y=ay,
        width=w,
        height=h,
        stroke=_arrow_ink(),
        fill="transparent",
        index=index,
        stroke_width=stroke_width,
        stroke_style=stroke_style,
    )
    el.update({
        "points": rel,
        "lastCommittedPoint": None,
        "startBinding": {"elementId": start_id, "focus": 0, "gap": 8},
        "endBinding": {"elementId": end_id, "focus": 0, "gap": 8},
        "startArrowhead": None,
        "endArrowhead": "arrow",
    })
    return el


# ----------------------------------------------------------------------------
# Layout assembly
# ----------------------------------------------------------------------------
def build_excalidraw(model: dict[str, Any], gv: dict[str, Any]) -> dict[str, Any]:
    direction = model.get("direction", "TB")
    sections = model.get("sections", []) or []
    section_labels = {s["id"]: s.get("label", s["id"]) for s in sections}
    evidence = model.get("evidence", []) or []
    title = model.get("title")
    subtitle = model.get("subtitle")

    # Canvas height in graphviz px (we'll flip y against this).
    gv_bb = _parse_bb(gv["bb"])  # (0,0, W, H)
    canvas_h = gv_bb[3]

    # First pass: collect nodes and clusters and their Excalidraw rects.
    node_rect_by_id: dict[str, dict[str, Any]] = {}
    cluster_bbox_by_id: dict[str, tuple[float, float, float, float]] = {}

    def walk_objects(objs: list[dict[str, Any]]) -> None:
        for obj in objs:
            name = obj.get("name", "")
            if name.startswith("cluster_"):
                # raw cluster id before sanitisation is the suffix; but we need to
                # match against the original section ids. Safer: match on label.
                bb = _parse_bb(obj["bb"])
                label = obj.get("label", "")
                # Find section id by label.
                match_sid = None
                for s in sections:
                    if s.get("label", s["id"]) == label:
                        match_sid = s["id"]
                        break
                if match_sid is None:
                    # Fall back: try to match via sanitised-id reconstruction.
                    safe_suffix = name[len("cluster_"):]
                    for s in sections:
                        if re.sub(r"[^A-Za-z0-9_]", "_", s["id"]) == safe_suffix:
                            match_sid = s["id"]
                            break
                if match_sid is not None:
                    cluster_bbox_by_id[match_sid] = bb
                # Recurse.
                if obj.get("objects"):
                    walk_objects(obj["objects"])
            else:
                # Node.
                obj_name = obj.get("name", "")
                if obj_name:
                    # position is the centre in graphviz px.
                    pos = obj.get("pos", "0,0")
                    cx, cy = [float(v) for v in pos.split(",")]
                    # width/height in inches * 72 = px.
                    w_in = float(obj.get("width", NODE_W_IN))
                    h_in = float(obj.get("height", NODE_H_IN))
                    w = w_in * 72
                    h = h_in * 72
                    # Graphviz y is up. Convert centre-y to top-left and flip.
                    top_left_x = cx - w / 2
                    top_left_y_gv = cy + h / 2  # top is greater y in gv
                    # Flip to Excalidraw coords and offset.
                    x = top_left_x + CANVAS_PAD_X
                    y = _flip_y(top_left_y_gv, canvas_h) + CANVAS_PAD_Y
                    node_rect_by_id[obj_name] = {
                        "x": x, "y": y, "w": w, "h": h, "cx": cx, "cy": cy,
                    }

    walk_objects(gv.get("objects", []))

    # Predict total element count for zero-padding width.
    est_nodes = len(model["nodes"])
    est_edges = len(model["edges"])
    est_sections = len(sections)
    est_evidence = len(evidence)
    # rough count: sections (rect + label) + column headers + nodes (rect + label)
    # + edges (arrow + optional label) + evidence (rect + text) + title + subtitle.
    est_total = (
        est_sections * 3  # rect + label + column header
        + est_nodes * 2
        + est_edges * 2
        + est_evidence * 2
        + 2  # title + subtitle
        + 10  # headroom
    )
    pad_w = max(2, len(str(est_total)))

    elements: list[dict[str, Any]] = []
    idx = 0

    def next_index() -> str:
        nonlocal idx
        s = _pad(idx, pad_w)
        idx += 1
        return s

    typo = _typography()
    title_size = int(typo.get("titleSize", 36))
    subtitle_size = int(typo.get("subtitleSize", 18))
    section_header_size = int(typo.get("sectionHeaderSize", 18))
    body_size = int(typo.get("bodySize", 16))
    arrow_label_size = int(typo.get("arrowLabelSize", 14))
    shapes_cfg = _shapes_cfg()
    node_stroke_w = int(shapes_cfg.get("strokeWidth", 2))
    frame_stroke_w = int(shapes_cfg.get("frameStrokeWidth", 1))
    arrow_stroke_w = int(shapes_cfg.get("arrowStrokeWidth", node_stroke_w))

    # --- Title / subtitle block -------------------------------------------
    if title:
        elements.append(
            make_free_text(
                el_id="title-block",
                x=40,
                y=30,
                text=title,
                font_size=title_size,
                index=next_index(),
            )
        )
    if subtitle:
        elements.append(
            make_free_text(
                el_id="subtitle-block",
                x=40,
                y=80,
                text=subtitle,
                font_size=subtitle_size,
                index=next_index(),
                stroke="#495057",
            )
        )

    # --- Section frames (dashed rects) ------------------------------------
    # For LR diagrams we emit uppercase column headers above the frame
    # instead of the redundant in-frame label.
    use_column_headers = (direction == "LR" and bool(sections))
    section_anchor: dict[str, dict[str, float]] = {}
    for s in sections:
        sid = s["id"]
        bb = cluster_bbox_by_id.get(sid)
        if not bb:
            continue
        x0, y0, x1, y1 = bb
        # Convert the two corners; note graphviz y is up so the top edge
        # is max_y in graphviz and the bottom is min_y.
        ex_x = x0 + CANVAS_PAD_X
        ex_y = _flip_y(y1, canvas_h) + CANVAS_PAD_Y
        ex_w = x1 - x0
        ex_h = y1 - y0
        frame_id = f"frame-{sid}"
        label_id = f"frame-{sid}-label" if not use_column_headers else None
        # Dashed rectangle frame.
        elements.append(
            make_rect(
                el_id=frame_id,
                x=ex_x,
                y=ex_y,
                w=ex_w,
                h=ex_h,
                stroke=_frame_stroke(),
                fill="transparent",
                index=next_index(),
                bound_text_id=label_id,
                stroke_width=frame_stroke_w,
                stroke_style="dashed",
            )
        )
        # Label inside top-left corner (skipped when column headers in use).
        if label_id is not None:
            lbl_text = section_labels.get(sid, sid)
            fs = section_header_size
            w = _estimate_text_width(lbl_text, fs)
            h = _text_height(lbl_text, fs)
            baseline = int(round(fs * 0.9))
            lbl_el = _base_element(
                el_id=label_id,
                el_type="text",
                x=ex_x + 12,
                y=ex_y + 4,
                width=w,
                height=h,
                stroke=_text_ink(),
                fill="transparent",
                index=next_index(),
                stroke_width=1,
            )
            lbl_el.update({
                "text": lbl_text,
                "originalText": lbl_text,
                "fontSize": fs,
                "fontFamily": int(typo.get("fontFamily", 2)),
                "textAlign": "left",
                "verticalAlign": "top",
                "baseline": baseline,
                "containerId": frame_id,
                "lineHeight": 1.25,
                "autoResize": True,
            })
            elements.append(lbl_el)
        section_anchor[sid] = {"x": ex_x, "y": ex_y, "w": ex_w, "h": ex_h}

    # --- Column headers for LR diagrams with sections ---------------------
    if use_column_headers:
        for s in sections:
            sid = s["id"]
            a = section_anchor.get(sid)
            if not a:
                continue
            header_text = section_labels.get(sid, sid).upper()
            # Position above the frame.
            header_y = max(a["y"] - 32, CANVAS_PAD_Y - 40)
            hdr_id = f"col-header-{sid}"
            elements.append(
                make_free_text(
                    el_id=hdr_id,
                    x=a["x"],
                    y=header_y,
                    text=header_text,
                    font_size=section_header_size,
                    index=next_index(),
                )
            )

    # --- Nodes and their bound text labels --------------------------------
    # We need to collect arrow bindings per rect for boundElements. Build a
    # map from (from_id, to_id) -> arrow id as we go.
    node_boundelements: dict[str, list[dict[str, str]]] = {}
    # Pre-assign node rect ids and text ids so edges can refer to them.
    node_id_map = {n["id"]: f"node-{re.sub(r'[^A-Za-z0-9_-]', '_', n['id'])}"
                   for n in model["nodes"]}
    # Reserve two indices per node (rect then text) but we assign on the fly.

    # Emit rectangles first (they need to be painted behind labels; and we
    # will later patch boundElements with arrow ids).
    pending_node_elements: dict[str, dict[str, Any]] = {}
    pending_text_for: dict[str, dict[str, Any]] = {}

    palette_map = _colors()
    default_palette = palette_map.get("service", _DEFAULT_THEME["colors"]["service"])
    for n in model["nodes"]:
        rect_id = node_id_map[n["id"]]
        text_id = rect_id + "-label"
        kind = (n.get("kind") or "service").lower()
        palette = palette_map.get(kind, default_palette)
        pos = node_rect_by_id.get(n["id"])
        if pos is None:
            # Node missing from graphviz output; synthesise at origin so the
            # file is still valid (should not happen for well-formed input).
            continue
        rect_el = make_rect(
            el_id=rect_id,
            x=pos["x"],
            y=pos["y"],
            w=pos["w"],
            h=pos["h"],
            stroke=palette["stroke"],
            fill=palette["fill"],
            index=next_index(),
            bound_text_id=text_id,
            stroke_width=node_stroke_w,
        )
        pending_node_elements[n["id"]] = rect_el
        elements.append(rect_el)
        # Bound label.
        label_text = n["label"]
        # Shrink font from body+4 down to body floor (auto-fit).
        fs = body_size + 4
        floor = max(14, body_size - 2)
        while _estimate_text_width(label_text, fs) > pos["w"] - 16 and fs > floor:
            fs -= 2
        txt_el = make_bound_text(
            el_id=text_id,
            container_id=rect_id,
            container_x=pos["x"],
            container_y=pos["y"],
            container_w=pos["w"],
            container_h=pos["h"],
            text=label_text,
            font_size=fs,
            index=next_index(),
        )
        pending_text_for[n["id"]] = txt_el
        elements.append(txt_el)
        node_boundelements[n["id"]] = rect_el["boundElements"]

    # --- Edges ------------------------------------------------------------
    # Build a gvid -> node name map and an ordered list of gv edges.
    def _gv_node_names(objs: list[dict[str, Any]]) -> dict[int, str]:
        m: dict[int, str] = {}
        def rec(os_: list[dict[str, Any]]) -> None:
            for o in os_:
                if o.get("name", "").startswith("cluster_"):
                    if o.get("objects"):
                        rec(o["objects"])
                else:
                    if "_gvid" in o:
                        m[o["_gvid"]] = o["name"]
        rec(objs)
        return m

    gvid_to_name = _gv_node_names(gv.get("objects", []))
    gv_edges = gv.get("edges", [])
    # Pair input edges to gv edges positionally (dot preserves input order).
    for i, e in enumerate(model["edges"]):
        gv_edge = gv_edges[i] if i < len(gv_edges) else None
        from_id = e["from"]
        to_id = e["to"]
        from_rect_id = node_id_map[from_id]
        to_rect_id = node_id_map[to_id]
        arrow_id = f"arr-{i:03d}"

        # Derive waypoints from gv edge "pos" (spline control list).
        # Format: "e,ex,ey x0,y0 x1,y1 ...". The "e,.." prefix is the end
        # arrowhead target. For splines=ortho the remaining list is usually
        # a polyline of 4+ points. We convert every coordinate through the
        # y-flip, then simplify duplicates.
        points_abs: list[list[float]] = []
        if gv_edge and gv_edge.get("pos"):
            pos_str = gv_edge["pos"]
            parts = pos_str.split()
            end_point: list[float] | None = None
            pts: list[list[float]] = []
            for p in parts:
                if p.startswith("e,"):
                    _, xy = p.split(",", 1)
                    ex, ey = [float(v) for v in xy.split(",")]
                    end_point = [ex, ey]
                elif p.startswith("s,"):
                    _, xy = p.split(",", 1)
                    # start arrowhead — ignore, we already know start
                    continue
                else:
                    x, y = [float(v) for v in p.split(",")]
                    pts.append([x, y])
            if end_point is not None:
                pts.append(end_point)
            # Convert to Excalidraw coords.
            for x, y in pts:
                ex_x = x + CANVAS_PAD_X
                ex_y = _flip_y(y, canvas_h) + CANVAS_PAD_Y
                points_abs.append([ex_x, ex_y])

        # Fallback: straight line centre-to-centre.
        if len(points_abs) < 2:
            a = node_rect_by_id.get(from_id)
            b = node_rect_by_id.get(to_id)
            if a and b:
                points_abs = [
                    [a["x"] + a["w"] / 2, a["y"] + a["h"] / 2],
                    [b["x"] + b["w"] / 2, b["y"] + b["h"] / 2],
                ]
            else:
                points_abs = [[0, 0], [100, 0]]

        # Snap to 10px grid to kill sub-pixel jitter from graphviz.
        for pt in points_abs:
            pt[0] = round(pt[0] / 10) * 10
            pt[1] = round(pt[1] / 10) * 10

        # Collapse duplicate points after snapping.
        deduped: list[list[float]] = [points_abs[0]]
        for pt in points_abs[1:]:
            if pt[0] != deduped[-1][0] or pt[1] != deduped[-1][1]:
                deduped.append(pt)

        # Collapse collinear runs (same x or same y in sequence).
        simplified: list[list[float]] = [deduped[0]]
        for pt in deduped[1:]:
            if len(simplified) >= 2:
                a = simplified[-2]
                b = simplified[-1]
                if a[1] == b[1] == pt[1]:  # horizontal run
                    simplified[-1] = pt
                    continue
                if a[0] == b[0] == pt[0]:  # vertical run
                    simplified[-1] = pt
                    continue
            simplified.append(pt)

        # For near-straight arrows (2 points, small offset), snap to
        # perfectly horizontal or vertical so they don't look kinked.
        if len(simplified) == 2:
            dx = abs(simplified[1][0] - simplified[0][0])
            dy = abs(simplified[1][1] - simplified[0][1])
            if dy > 0 and dy < 30 and dx > dy * 3:
                simplified[1][1] = simplified[0][1]
            elif dx > 0 and dx < 30 and dy > dx * 3:
                simplified[1][0] = simplified[0][0]

        style = e.get("style", "solid")
        stroke_style = {
            "solid": "solid", "dashed": "dashed", "dotted": "dotted"
        }.get(style, "solid")
        arrow_el = make_arrow(
            el_id=arrow_id,
            start_id=from_rect_id,
            end_id=to_rect_id,
            points=simplified,
            index=next_index(),
            stroke_style=stroke_style,
            stroke_width=arrow_stroke_w,
        )
        elements.append(arrow_el)

        # Register arrow on both node rects' boundElements.
        for rid in (from_id, to_id):
            rect_bound = node_boundelements.get(rid)
            if rect_bound is not None:
                rect_bound.append({"id": arrow_id, "type": "arrow"})

        # Optional free-floating label at midpoint of the longest segment.
        if e.get("label"):
            mid = _midpoint_of_longest_segment(simplified)
            lbl_id = f"lbl-{arrow_id}"
            elements.append(
                make_free_text(
                    el_id=lbl_id,
                    x=mid[0] + 6,
                    y=mid[1] - 22,
                    text=e["label"],
                    font_size=arrow_label_size,
                    index=next_index(),
                )
            )

    # --- Evidence artifacts -----------------------------------------------
    for i, ev in enumerate(evidence):
        anchor = ev.get("anchor_near")
        text = ev.get("text", "")
        position = ev.get("position", "right")
        a = node_rect_by_id.get(anchor) if anchor else None
        if not a:
            continue
        fs = arrow_label_size
        # Estimate box size from text.
        longest = max((len(line) for line in text.split("\n")), default=1)
        box_w = max(160, int(longest * fs * 0.65) + 24)
        box_h = max(60, int(_text_height(text, fs)) + 24)
        if position == "right":
            ex = a["x"] + a["w"] + 32
            ey = a["y"]
        elif position == "left":
            ex = a["x"] - box_w - 32
            ey = a["y"]
        elif position == "below":
            ex = a["x"]
            ey = a["y"] + a["h"] + 24
        else:  # above
            ex = a["x"]
            ey = a["y"] - box_h - 24
        rect_id = f"evidence-{i}"
        text_id = f"evidence-{i}-text"
        elements.append(
            make_rect(
                el_id=rect_id,
                x=ex,
                y=ey,
                w=box_w,
                h=box_h,
                stroke=_evidence_stroke(),
                fill=_evidence_fill(),
                index=next_index(),
                bound_text_id=text_id,
                stroke_width=node_stroke_w,
            )
        )
        elements.append(
            make_bound_text(
                el_id=text_id,
                container_id=rect_id,
                container_x=ex,
                container_y=ey,
                container_w=box_w,
                container_h=box_h,
                text=text,
                font_size=fs,
                index=next_index(),
                font_family=3,
                stroke=_evidence_stroke(),
            )
        )

    return {
        "type": "excalidraw",
        "version": 2,
        "source": "excalidraw-skill-graphviz",
        "elements": elements,
        "appState": {
            "gridSize": None,
            "viewBackgroundColor": THEME.get("canvas", {}).get(
                "backgroundColor", "#ffffff"
            ),
        },
        "files": {},
    }


def _midpoint_of_longest_segment(points: list[list[float]]) -> list[float]:
    if len(points) < 2:
        return [0.0, 0.0]
    longest = 0.0
    best = [(points[0][0] + points[1][0]) / 2, (points[0][1] + points[1][1]) / 2]
    for a, b in zip(points, points[1:]):
        d = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
        if d > longest:
            longest = d
            best = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]
    return best


# ----------------------------------------------------------------------------
# Entrypoint
# ----------------------------------------------------------------------------
def run(
    input_path: str,
    output_path: str,
    *,
    seed: int | None = None,
    theme_path: str | None = None,
) -> None:
    if seed is not None:
        random.seed(seed)
    # Reload theme so callers can override per-invocation. Honour env var
    # so tests and subprocesses can inject a custom theme without mutating
    # the skill root.
    global THEME
    env_theme = theme_path or os.environ.get("EXCALIDRAW_THEME")
    THEME = load_theme(env_theme) if env_theme else load_theme()
    with open(input_path, "r", encoding="utf-8") as f:
        model = json.load(f)
    validate_input(model)
    dot_src = build_dot(model)
    gv = run_dot(dot_src)
    diagram = build_excalidraw(model, gv)
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(diagram, f, indent=2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Graphviz-backed layout for Excalidraw architecture diagrams. "
            "Emits an Excalidraw JSON file with orthogonal arrow routing "
            "and Oli's styling rules."
        ),
    )
    parser.add_argument("--input", required=True, help="path to semantic-model JSON")
    parser.add_argument("--output", required=True, help="path to .excalidraw to write")
    parser.add_argument("--seed", type=int, default=None, help="random seed for element seeds")
    parser.add_argument("--theme", default=None, help="override path to theme.json")
    args = parser.parse_args(argv)
    try:
        run(args.input, args.output, seed=args.seed, theme_path=args.theme)
    except Exception as e:  # noqa: BLE001
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
