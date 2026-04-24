#!/usr/bin/env python3
"""
render.py

Render an .excalidraw file to PNG via headless Playwright + Chromium.

Replaces the previous Chrome DevTools MCP / ad-hoc puppeteer-core paths.

Flow:
  1. Launch headless Chromium via Playwright.
  2. Navigate to https://excalidraw.com.
  3. Wait for the canvas to be present.
  4. Dispatch a synthetic drop event carrying the .excalidraw file as a
     File object on the canvas. localStorage injection is intentionally
     NOT used — current Excalidraw hangs on "Loading scene…" when the
     IndexedDB hand-off never fires.
  5. Press Shift+1 to fit-to-viewport.
  6. Wait 500ms for the render to settle.
  7. Screenshot the canvas at the requested size.
  8. Close the browser.

Usage:
    uv run python scripts/render.py --input <file.excalidraw> \
        --output <file.png> [--width 2400] [--height 1600]

JSON on stdout:
    {"ok": true, "output": "<path>", "bytes": N}
or, on failure (exit 1):
    {"ok": false, "error": "..."}
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
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


EXCALIDRAW_URL = "https://excalidraw.com"


async def render_async(
    input_path: str,
    output_path: str,
    width: int,
    height: int,
) -> dict:
    in_path = Path(input_path).resolve()
    out_path = Path(output_path).resolve()
    if not in_path.exists():
        return {"ok": False, "error": f"input not found: {in_path}"}
    out_path.parent.mkdir(parents=True, exist_ok=True)

    file_text = in_path.read_text(encoding="utf-8")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=2,
        )
        page = await context.new_page()
        try:
            await page.goto(EXCALIDRAW_URL, wait_until="domcontentloaded")
            # Excalidraw lazy-loads heavy chunks; wait for the drawing canvas.
            await page.wait_for_selector("canvas", timeout=30_000)
            # Dismiss any first-run welcome dialogs by pressing Escape.
            try:
                await page.keyboard.press("Escape")
            except Exception:
                pass

            # Dispatch a synthetic drop event carrying the file contents.
            # The page-side script builds a File via the page's own File
            # constructor so Excalidraw's drop handler treats it as native.
            await page.evaluate(
                """
                async ({ fileText }) => {
                  const canvas = document.querySelector('canvas');
                  if (!canvas) throw new Error('no canvas element');
                  const file = new File([fileText], 'diagram.excalidraw',
                    { type: 'application/json' });
                  const dt = new DataTransfer();
                  dt.items.add(file);
                  const drop = new DragEvent('drop', {
                    bubbles: true, cancelable: true, dataTransfer: dt,
                  });
                  canvas.dispatchEvent(drop);
                }
                """,
                {"fileText": file_text},
            )

            # Let the file load before fit-to-viewport.
            await page.wait_for_timeout(800)
            # Shift+1 = "Reset zoom" / fit-to-viewport in Excalidraw.
            await page.keyboard.press("Shift+1")
            await page.wait_for_timeout(500)

            # Screenshot the full viewport (Excalidraw covers it).
            png_bytes = await page.screenshot(
                path=str(out_path),
                full_page=False,
                omit_background=False,
            )
            return {
                "ok": True,
                "output": str(out_path),
                "bytes": len(png_bytes),
            }
        finally:
            await context.close()
            await browser.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render .excalidraw to PNG via headless Playwright.",
    )
    parser.add_argument("--input", required=True, help="path to .excalidraw")
    parser.add_argument("--output", required=True, help="path to .png to write")
    parser.add_argument("--width", type=int, default=2400, help="viewport px")
    parser.add_argument("--height", type=int, default=1600, help="viewport px")
    args = parser.parse_args(argv)

    try:
        result = asyncio.run(render_async(
            args.input, args.output, args.width, args.height
        ))
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(e)}))
        return 1

    print(json.dumps(result))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
