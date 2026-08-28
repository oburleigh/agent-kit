import argparse
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

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


def classify_git_diff(
    base: str, head: str, *, cwd: Path | str | None = None
) -> Scope:
    result = subprocess.run(
        ["git", "diff", "--name-only", "-z", "--no-renames", f"{base}...{head}"],
        cwd=cwd,
        check=True,
        capture_output=True,
    )
    paths = [
        value.decode("utf-8", errors="surrogateescape")
        for value in result.stdout.split(b"\0")
    ]
    return classify_paths(paths)


def print_scope(scope: Scope) -> None:
    print(f"distribution={str(scope.distribution).lower()}")
    print(f"python={str(scope.python).lower()}")
    print(f"typescript={str(scope.typescript).lower()}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument(
        "--null",
        action="store_true",
        help="read NUL-delimited paths, as emitted by git diff --name-only -z",
    )
    arguments = parser.parse_args(argv)
    if (arguments.base is None) != (arguments.head is None):
        parser.error("--base and --head must be provided together")

    if arguments.base is not None:
        scope = classify_git_diff(arguments.base, arguments.head)
    else:
        separator = b"\0" if arguments.null else b"\n"
        paths = [
            value.decode("utf-8", errors="surrogateescape")
            for value in sys.stdin.buffer.read().split(separator)
        ]
        scope = classify_paths(paths)

    print_scope(scope)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
