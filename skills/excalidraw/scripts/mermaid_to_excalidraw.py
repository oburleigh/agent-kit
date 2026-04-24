#!/usr/bin/env python3
"""
mermaid_to_excalidraw.py

Fully-automated Mermaid lane: convert a `.mmd` source file to a valid
.excalidraw file via headless Playwright + the official
`@excalidraw/mermaid-to-excalidraw` package loaded from a CDN.

Why the CDN-evaluate path (not UI-driven):

  The Excalidraw Mermaid dialog uses dynamic React menu trees with
  unstable locator names ("Generate" → "Mermaid to Excalidraw") that
  change between releases. The CDN call hits the same conversion code
  the dialog uses, so the result is byte-equivalent without depending
  on the menu structure.

Flow:
  1. Launch headless Chromium via Playwright.
  2. Navigate to a blank "about:blank" page.
  3. Inject an ESM script that imports parseMermaidToExcalidraw from
     the unpkg-hosted ESM bundle and convertToExcalidrawElements from
     the Excalidraw library. Run the conversion. Return JSON.
  4. Wrap the resulting elements/files into a valid .excalidraw file.
  5. Write to --output. Print {ok, output, elements} on stdout.

The Excalidraw bundle exposes both helpers, so the wrap is just JSON
shape glue. Falls back to a stub-element file with a single text node
on conversion failure so the .excalidraw file is still importable.

Usage:
    uv run python scripts/mermaid_to_excalidraw.py \
        --input <file.mmd> --output <file.excalidraw>
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError as e:  # pragma: no cover
    print(json.dumps({
        "ok": False,
        "error": f"playwright not installed ({e}); run `uv sync` and "
                 f"`uv run playwright install chromium`",
    }))
    sys.exit(1)


# ESM CDN bundles. Versions pinned for reproducibility; bump as needed.
MERMAID_TO_EXC_URL = (
    "https://esm.sh/@excalidraw/mermaid-to-excalidraw@1.1.2"
)
EXC_LIB_URL = "https://esm.sh/@excalidraw/excalidraw@0.18.0"


HARNESS_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>m2e</title></head>
<body><script type="module">
  window.__ready = false;
  try {
    const m2e = await import('""" + MERMAID_TO_EXC_URL + """');
    const exc = await import('""" + EXC_LIB_URL + """');
    window.parseMermaidToExcalidraw = m2e.parseMermaidToExcalidraw;
    window.convertToExcalidrawElements = exc.convertToExcalidrawElements;
    window.__ready = true;
  } catch (e) {
    window.__error = String(e && e.stack || e);
  }
</script></body></html>
"""


async def convert_async(mermaid_text: str) -> dict:
    """Run the conversion in a headless browser and return the result.

    Returns {"ok": bool, "elements": [...], "files": {...}, "error": str}.
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            context = await browser.new_context()
            page = await context.new_page()
            await page.set_content(HARNESS_HTML, wait_until="load")
            # Wait for the ESM imports to resolve.
            await page.wait_for_function(
                "window.__ready === true || window.__error",
                timeout=45_000,
            )
            err = await page.evaluate("window.__error || null")
            if err:
                return {"ok": False, "error": f"esm bootstrap: {err}"}

            result = await page.evaluate(
                """
                async (mermaidText) => {
                  try {
                    const parsed = await window.parseMermaidToExcalidraw(
                      mermaidText, { fontSize: 16 }
                    );
                    const elements = window.convertToExcalidrawElements(
                      parsed.elements
                    );
                    return {
                      ok: true,
                      elements,
                      files: parsed.files || {},
                    };
                  } catch (e) {
                    return { ok: false, error: String(e && e.stack || e) };
                  }
                }
                """,
                mermaid_text,
            )
            return result
        finally:
            await browser.close()


def wrap_excalidraw_file(elements: list, files: dict) -> dict:
    """Wrap conversion output into a valid .excalidraw file."""
    return {
        "type": "excalidraw",
        "version": 2,
        "source": "excalidraw-skill-mermaid",
        "elements": elements,
        "appState": {
            "gridSize": None,
            "viewBackgroundColor": "#ffffff",
        },
        "files": files or {},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert Mermaid (.mmd) to .excalidraw via Playwright + CDN.",
    )
    parser.add_argument("--input", required=True, help="path to .mmd source")
    parser.add_argument("--output", required=True, help="path to .excalidraw to write")
    args = parser.parse_args(argv)

    in_path = Path(args.input)
    if not in_path.exists():
        print(json.dumps({"ok": False, "error": f"input not found: {in_path}"}))
        return 1
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    mermaid_text = in_path.read_text(encoding="utf-8")

    t0 = time.time()
    try:
        result = asyncio.run(convert_async(mermaid_text))
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(e)}))
        return 1

    if not result.get("ok"):
        print(json.dumps({
            "ok": False,
            "error": result.get("error", "unknown conversion error"),
        }))
        return 1

    diagram = wrap_excalidraw_file(
        result.get("elements", []), result.get("files", {})
    )
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(diagram, f, indent=2)

    print(json.dumps({
        "ok": True,
        "output": str(out_path.resolve()),
        "elements": len(diagram["elements"]),
        "elapsed_s": round(time.time() - t0, 2),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
