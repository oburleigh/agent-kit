#!/usr/bin/env python3
"""
run_evals.py

Python port of the legacy Node eval runner. Pure stdlib. Reads
`evals/evals.json` and scaffolds a workspace with `with_skill/` and
`without_skill/` subdirs per case, each carrying a TODO.md and a
timing.json. Grading happens out-of-band by a render+inspect subagent.

Usage:
    uv run python scripts/run_evals.py --workspace /tmp/excalidraw-ws-N
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def build_grading_prompt(rubric: dict[str, str]) -> str:
    """Same contract as the legacy buildGradingPrompt."""
    dims = "\n".join(f"- {k}: {v}" for k, v in rubric.items())
    return (
        "You are grading an Excalidraw diagram. Default score per "
        "dimension is 0; require concrete evidence to award 1 (partial) "
        "or 2 (pass).\n"
        'Return strict JSON: {"<dim>":{"score":N,"evidence":"..."},...}.\n\n'
        f"Rubric:\n{dims}"
    )


def score_from_grading(grading: dict[str, dict]) -> dict[str, int]:
    dims = list(grading.values())
    total = sum(int(d.get("score", 0) or 0) for d in dims)
    return {"total": total, "max": len(dims) * 2}


def scaffold(workspace: Path, evals_path: Path) -> dict:
    with open(evals_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    workspace.mkdir(parents=True, exist_ok=True)
    results = []
    for case in spec.get("evals", []):
        cid = case["id"]
        for lane in ("with_skill", "without_skill"):
            d = workspace / f"eval-{cid}" / lane
            (d / "outputs").mkdir(parents=True, exist_ok=True)
            todo = "\n".join([
                f"# {cid} ({lane})",
                "",
                "## Prompt",
                case["prompt"],
                "",
                ("## How to run\nRun your agent WITH the excalidraw skill on this prompt. "
                 "Save outputs to outputs/.")
                if lane == "with_skill" else
                ("## How to run\nRun a fresh agent session WITHOUT the excalidraw "
                 "skill. Save outputs to outputs/."),
                "",
                "## Grading",
                ("After both lanes run, a subagent renders each output via "
                 "scripts/render.py, inspects the PNG, and scores against the "
                 "rubric in evals/evals.json. Save to grading.json here."),
            ])
            (d / "TODO.md").write_text(todo, encoding="utf-8")
            (d / "timing.json").write_text(
                json.dumps({"created_at": int(time.time() * 1000)}),
                encoding="utf-8",
            )
        results.append({"id": cid})

    benchmark = workspace / "benchmark.json"
    benchmark.write_text(
        json.dumps(
            {"created_at": int(time.time() * 1000), "results": results},
            indent=2,
        ),
        encoding="utf-8",
    )
    return {"workspace": str(workspace), "cases": len(results)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a with_skill/without_skill eval workspace."
    )
    parser.add_argument(
        "--workspace",
        default="excalidraw-workspace/iteration-1",
        help="path to workspace root",
    )
    args = parser.parse_args(argv)

    skill_root = Path(__file__).resolve().parent.parent
    evals_path = skill_root / "evals" / "evals.json"
    if not evals_path.exists():
        print(json.dumps({"ok": False, "error": f"evals.json not found at {evals_path}"}),
              file=sys.stderr)
        return 1

    try:
        result = scaffold(Path(args.workspace).resolve(), evals_path)
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(e)}), file=sys.stderr)
        return 1

    print(json.dumps({"ok": True, **result}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
