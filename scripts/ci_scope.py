import argparse
import sys
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable


MARKDOWN_SUFFIXES = {".md", ".markdown", ".mdx"}
VALIDATION_WORKFLOW = ".github/workflows/validation.yml"


@dataclass(frozen=True)
class Scope:
    distribution: bool
    python: bool
    typescript: bool


def is_within(path: str, root: str) -> bool:
    return path == root or path.startswith(f"{root}/")


def is_skill_path(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return is_within(path, "skills") or (
        len(parts) >= 3 and parts[0] == "plugins" and parts[2] == "skills"
    )


def classify_paths(paths: Iterable[str]) -> Scope:
    distribution = False
    python = False
    typescript = False

    for raw_path in paths:
        path = raw_path.removeprefix("./")
        if not path:
            continue

        if path == VALIDATION_WORKFLOW:
            return Scope(True, True, True)

        markdown = PurePosixPath(path).suffix.lower() in MARKDOWN_SUFFIXES
        distribution |= not markdown or is_skill_path(path)
        python |= is_within(path, "skills/python-scaffold") or is_within(
            path, "plugins/python-scaffold/skills/python-scaffold"
        )
        typescript |= is_within(path, "skills/typescript-scaffold") or is_within(
            path, "plugins/typescript-scaffold/skills/typescript-scaffold"
        )

    return Scope(distribution, python, typescript)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--null",
        action="store_true",
        help="read NUL-delimited paths, as emitted by git diff --name-only -z",
    )
    arguments = parser.parse_args(argv)
    separator = b"\0" if arguments.null else b"\n"
    paths = [value.decode("utf-8") for value in sys.stdin.buffer.read().split(separator)]
    scope = classify_paths(paths)

    print(f"distribution={str(scope.distribution).lower()}")
    print(f"python={str(scope.python).lower()}")
    print(f"typescript={str(scope.typescript).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
