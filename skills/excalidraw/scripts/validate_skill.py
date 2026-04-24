#!/usr/bin/env python3
"""
validate_skill.py

Python port of the legacy Node validator. Pure stdlib. Checks:

  1. SKILL.md exists at <skill>/SKILL.md.
  2. SKILL.md has YAML frontmatter with `name` and `description` keys.
  3. SKILL.md is fewer than 400 lines.
  4. Every reference file under <skill>/references/ is mentioned by
     name somewhere in SKILL.md (catches stale refs and orphan docs).
  5. theme.json (if present) is valid JSON.

Emits a JSON summary on stdout when ok. On failure exits 1 with the
error list inside the JSON.

Usage:
    uv run python scripts/validate_skill.py --skill .
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LINE_LIMIT = 400


def parse_frontmatter(text: str) -> dict[str, str]:
    """Minimal YAML frontmatter parser — `key: value` lines only."""
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    if len(lines) < 2:
        return {}
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}
    out: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip()
    return out


def list_reference_files(refs_dir: Path) -> list[Path]:
    if not refs_dir.is_dir():
        return []
    out: list[Path] = []
    for p in sorted(refs_dir.iterdir()):
        if p.is_file():
            out.append(p)
    return out


def validate_skill(skill_root: Path) -> dict:
    errors: list[str] = []
    references: list[str] = []
    line_count = 0

    skill_md = skill_root / "SKILL.md"
    if not skill_md.exists():
        return {"ok": False, "errors": [f"SKILL.md not found at {skill_md}"]}

    content = skill_md.read_text(encoding="utf-8")
    line_count = len(content.splitlines())
    if line_count >= LINE_LIMIT:
        errors.append(
            f"SKILL.md has {line_count} lines — must be under {LINE_LIMIT}"
        )

    fm = parse_frontmatter(content)
    if not fm.get("name"):
        errors.append("SKILL.md frontmatter missing `name`")
    if not fm.get("description"):
        errors.append("SKILL.md frontmatter missing `description`")

    refs_dir = skill_root / "references"
    for ref in list_reference_files(refs_dir):
        rel = f"references/{ref.name}"
        references.append(rel)
        # Mention check: filename basename is acceptable too.
        if ref.name not in content and rel not in content:
            errors.append(f"reference {rel} not mentioned in SKILL.md")

    theme_path = skill_root / "theme.json"
    if theme_path.exists():
        try:
            json.loads(theme_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"theme.json invalid JSON: {e}")

    return {
        "ok": not errors,
        "errors": errors,
        "lineCount": line_count,
        "references": references,
        "name": fm.get("name"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate an Excalidraw-style skill directory."
    )
    parser.add_argument("--skill", default=".", help="path to skill root")
    args = parser.parse_args(argv)

    result = validate_skill(Path(args.skill).resolve())

    if not result["ok"]:
        print(json.dumps(
            {"ok": False, "errors": result["errors"]},
            indent=2,
        ), file=sys.stderr)
        return 1

    print(json.dumps({
        "ok": True,
        "name": result.get("name"),
        "lineCount": result["lineCount"],
        "references": result["references"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
