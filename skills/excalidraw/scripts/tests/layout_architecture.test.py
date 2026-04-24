#!/usr/bin/env python3
"""
Tests for scripts/layout_architecture.py.

Stdlib-only. Covers structural invariants of generated Excalidraw JSON:
bindings, roughness, fontFamily, index ordering, theme consumption,
overlap detection, section/frame creation.

Run directly:
    python3 scripts/tests/layout_architecture.test.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SCRIPTS_DIR.parent
SCRIPT_PATH = SCRIPTS_DIR / "layout_architecture.py"

sys.path.insert(0, str(SCRIPTS_DIR))
import layout_architecture as layout  # noqa: E402


def _run_script(
    input_model: dict,
    output_path: str,
    seed: int = 1,
    theme_path: str | None = None,
) -> None:
    """Write the model to a tempfile and invoke the script subprocess."""
    with tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(input_model, f)
        in_path = f.name
    try:
        cmd = [
            sys.executable,
            str(SCRIPT_PATH),
            "--input", in_path,
            "--output", output_path,
            "--seed", str(seed),
        ]
        if theme_path:
            cmd.extend(["--theme", theme_path])
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    finally:
        os.unlink(in_path)


def _load_diagram(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class TrivialTwoNodeGraph(unittest.TestCase):
    def setUp(self) -> None:
        if shutil.which("dot") is None:
            self.skipTest("graphviz `dot` not available")
        self.tmp = tempfile.mkdtemp(prefix="layout-arch-test-")
        self.out = os.path.join(self.tmp, "mini.excalidraw")
        _run_script(
            {
                "title": "Mini",
                "nodes": [
                    {"id": "a", "label": "Alpha", "kind": "service"},
                    {"id": "b", "label": "Beta", "kind": "datastore"},
                ],
                "edges": [{"from": "a", "to": "b", "label": "writes"}],
            },
            self.out,
        )
        self.diagram = _load_diagram(self.out)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_top_level_shape(self) -> None:
        self.assertEqual(self.diagram["type"], "excalidraw")
        self.assertEqual(self.diagram["version"], 2)
        self.assertIsInstance(self.diagram["elements"], list)
        self.assertIn("appState", self.diagram)

    def test_every_element_roughness_zero(self) -> None:
        for e in self.diagram["elements"]:
            self.assertEqual(e["roughness"], 0, f"non-zero roughness on {e['id']}")

    def test_every_text_has_ink_colour(self) -> None:
        for e in self.diagram["elements"]:
            if e["type"] == "text":
                self.assertNotEqual(e["strokeColor"], "transparent",
                                    f"text {e['id']} has transparent ink")

    def test_node_rects_bind_their_labels(self) -> None:
        rects = {e["id"]: e for e in self.diagram["elements"] if e["type"] == "rectangle"}
        texts = {e["id"]: e for e in self.diagram["elements"] if e["type"] == "text"}
        for text_id, text in texts.items():
            container_id = text.get("containerId")
            if container_id and container_id in rects:
                bound_ids = [b["id"] for b in rects[container_id]["boundElements"]]
                self.assertIn(text_id, bound_ids,
                              f"rect {container_id} missing bound text {text_id}")

    def test_arrow_bindings_point_to_real_ids(self) -> None:
        ids = {e["id"] for e in self.diagram["elements"]}
        arrows = [e for e in self.diagram["elements"] if e["type"] == "arrow"]
        for a in arrows:
            self.assertIn("startBinding", a)
            self.assertIn("endBinding", a)
            self.assertIn(a["startBinding"]["elementId"], ids)
            self.assertIn(a["endBinding"]["elementId"], ids)

    def test_no_rectangle_overlaps(self) -> None:
        rects = [e for e in self.diagram["elements"]
                 if e["type"] == "rectangle" and e["id"].startswith("node-")]
        for i, a in enumerate(rects):
            for b in rects[i + 1:]:
                overlap = not (
                    a["x"] + a["width"] <= b["x"] or
                    b["x"] + b["width"] <= a["x"] or
                    a["y"] + a["height"] <= b["y"] or
                    b["y"] + b["height"] <= a["y"]
                )
                self.assertFalse(overlap, f"{a['id']} overlaps {b['id']}")


class SectionedGraph(unittest.TestCase):
    def setUp(self) -> None:
        if shutil.which("dot") is None:
            self.skipTest("graphviz `dot` not available")
        self.tmp = tempfile.mkdtemp(prefix="layout-arch-test-")
        self.out = os.path.join(self.tmp, "sections.excalidraw")
        _run_script(
            {
                "title": "Sectioned",
                "direction": "LR",
                "nodes": [
                    {"id": "c", "label": "Client", "kind": "ui", "section": "edge"},
                    {"id": "g", "label": "Gateway", "kind": "service", "section": "core"},
                    {"id": "s", "label": "Service", "kind": "service", "section": "core"},
                    {"id": "d", "label": "DB", "kind": "datastore", "section": "core"},
                    {"id": "e", "label": "External", "kind": "external", "section": "out"},
                ],
                "edges": [
                    {"from": "c", "to": "g", "label": "HTTPS"},
                    {"from": "g", "to": "s", "label": "call"},
                    {"from": "s", "to": "d", "label": "query"},
                    {"from": "g", "to": "e", "label": "webhook", "style": "dashed"},
                ],
                "sections": [
                    {"id": "edge", "label": "EDGE"},
                    {"id": "core", "label": "CORE"},
                    {"id": "out", "label": "EXTERNAL"},
                ],
                "evidence": [
                    {"anchor_near": "d", "text": "db: postgres\npool: 20",
                     "position": "below"},
                ],
            },
            self.out,
            seed=2,
        )
        self.diagram = _load_diagram(self.out)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_section_frames_are_dashed_rectangles(self) -> None:
        frames = [e for e in self.diagram["elements"]
                  if e["type"] == "rectangle" and e["id"].startswith("frame-")]
        self.assertEqual(len(frames), 3)
        for f in frames:
            self.assertEqual(f["strokeStyle"], "dashed")
            self.assertEqual(f["backgroundColor"], "transparent")

    def test_evidence_uses_monospace_and_green(self) -> None:
        ev_texts = [e for e in self.diagram["elements"]
                    if e["type"] == "text" and e["id"].startswith("evidence-")]
        self.assertTrue(ev_texts)
        for t in ev_texts:
            self.assertEqual(t["fontFamily"], 3, "evidence text must be monospace")
            self.assertEqual(t["strokeColor"], "#22c55e")

    def test_non_evidence_text_uses_theme_font(self) -> None:
        expected_ff = layout._typography()["fontFamily"]
        non_evidence_texts = [
            e for e in self.diagram["elements"]
            if e["type"] == "text" and not e["id"].startswith("evidence-")
        ]
        for t in non_evidence_texts:
            self.assertEqual(
                t["fontFamily"], expected_ff,
                f"{t['id']} must use theme fontFamily {expected_ff}, got {t['fontFamily']}"
            )


class IndexOrdering(unittest.TestCase):
    def setUp(self) -> None:
        if shutil.which("dot") is None:
            self.skipTest("graphviz `dot` not available")
        self.tmp = tempfile.mkdtemp(prefix="layout-arch-test-")
        self.out = os.path.join(self.tmp, "idx.excalidraw")
        nodes = [{"id": f"n{i}", "label": f"N{i}", "kind": "service"} for i in range(12)]
        edges = [{"from": f"n{i}", "to": f"n{i+1}"} for i in range(11)]
        _run_script({"nodes": nodes, "edges": edges}, self.out, seed=3)
        self.diagram = _load_diagram(self.out)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_indices_are_zero_padded(self) -> None:
        indices = [e["index"] for e in self.diagram["elements"]]
        for idx in indices:
            self.assertRegex(idx, r"^a\d{2,}$", f"bad index format: {idx}")

    def test_indices_lex_order_matches_emission_order(self) -> None:
        indices = [e["index"] for e in self.diagram["elements"]]
        self.assertEqual(indices, sorted(indices))

    def test_indices_unique(self) -> None:
        indices = [e["index"] for e in self.diagram["elements"]]
        self.assertEqual(len(indices), len(set(indices)))


class InputValidation(unittest.TestCase):
    def test_rejects_missing_nodes(self) -> None:
        with self.assertRaises(ValueError):
            layout.validate_input({"edges": []})

    def test_rejects_duplicate_ids(self) -> None:
        with self.assertRaises(ValueError):
            layout.validate_input(
                {"nodes": [{"id": "a", "label": "A"}, {"id": "a", "label": "A2"}],
                 "edges": []}
            )

    def test_rejects_edge_to_unknown_node(self) -> None:
        with self.assertRaises(ValueError):
            layout.validate_input(
                {"nodes": [{"id": "a", "label": "A"}],
                 "edges": [{"from": "a", "to": "missing"}]}
            )


class ThemeConsumption(unittest.TestCase):
    """Theme overrides apply correctly without breaking invariants."""

    def setUp(self) -> None:
        if shutil.which("dot") is None:
            self.skipTest("graphviz `dot` not available")
        self.tmp = tempfile.mkdtemp(prefix="layout-arch-theme-")
        self.custom_theme = {
            "typography": {
                "fontFamily": 1, "titleSize": 50, "subtitleSize": 16,
                "sectionHeaderSize": 22, "bodySize": 16, "arrowLabelSize": 12,
            },
            "shapes": {"roundness": None, "strokeWidth": 3, "frameStrokeWidth": 2},
            "colors": {
                "service":   {"stroke": "#ff00ff", "fill": "#ffccff"},
                "datastore": {"stroke": "#6741d9", "fill": "#d0bfff"},
                "queue":     {"stroke": "#f08c00", "fill": "#ffec99"},
                "external":  {"stroke": "#868e96", "fill": "#dee2e6"},
                "ui":        {"stroke": "#2f9e44", "fill": "#b2f2bb"},
                "decision":  {"stroke": "#e8590c", "fill": "#ffd8a8"},
                "ai":        {"stroke": "#6d28d9", "fill": "#ddd6fe"},
                "error":     {"stroke": "#c92a2a", "fill": "#ffc9c9"},
                "evidence":  {"background": "#0b0b0b", "stroke": "#22c55e"},
                "frame":     {"stroke": "#999999"},
                "text":      {"stroke": "#000099"},
            },
            "canvas": {"backgroundColor": "#fffbe6"},
        }
        self.theme_path = os.path.join(self.tmp, "theme.json")
        with open(self.theme_path, "w", encoding="utf-8") as f:
            json.dump(self.custom_theme, f)
        self.out = os.path.join(self.tmp, "themed.excalidraw")
        _run_script(
            {
                "title": "Themed",
                "nodes": [
                    {"id": "a", "label": "Alpha", "kind": "service"},
                    {"id": "b", "label": "Beta", "kind": "datastore"},
                ],
                "edges": [{"from": "a", "to": "b", "label": "writes"}],
            },
            self.out,
            theme_path=self.theme_path,
        )
        self.diagram = _load_diagram(self.out)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_service_colour_uses_custom_theme(self) -> None:
        service = next(e for e in self.diagram["elements"]
                       if e["type"] == "rectangle" and e["id"] == "node-a")
        self.assertEqual(service["strokeColor"], "#ff00ff")
        self.assertEqual(service["backgroundColor"], "#ffccff")

    def test_text_font_family_from_theme(self) -> None:
        non_evidence_texts = [
            e for e in self.diagram["elements"]
            if e["type"] == "text" and not e["id"].startswith("evidence-")
        ]
        for t in non_evidence_texts:
            self.assertEqual(t["fontFamily"], 1, f"{t['id']} not Virgil")

    def test_canvas_background_from_theme(self) -> None:
        self.assertEqual(
            self.diagram["appState"]["viewBackgroundColor"], "#fffbe6"
        )

    def test_invariants_preserved_under_custom_theme(self) -> None:
        for el in self.diagram["elements"]:
            self.assertEqual(el["roughness"], 0)
            self.assertRegex(el["index"], r"^a\d{2,}$")


class ThemeFallback(unittest.TestCase):
    def test_missing_theme_falls_back_to_defaults(self) -> None:
        if shutil.which("dot") is None:
            self.skipTest("graphviz `dot` not available")
        tmp = tempfile.mkdtemp(prefix="layout-arch-fallback-")
        try:
            out = os.path.join(tmp, "fallback.excalidraw")
            ghost = os.path.join(tmp, "does-not-exist.json")
            _run_script(
                {
                    "nodes": [
                        {"id": "a", "label": "A", "kind": "service"},
                        {"id": "b", "label": "B", "kind": "service"},
                    ],
                    "edges": [{"from": "a", "to": "b"}],
                },
                out,
                theme_path=ghost,
            )
            d = _load_diagram(out)
            svc = next(e for e in d["elements"]
                       if e["type"] == "rectangle" and e["id"] == "node-a")
            self.assertEqual(svc["strokeColor"], "#1971c2")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
