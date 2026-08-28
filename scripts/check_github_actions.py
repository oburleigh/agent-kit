import re
import sys
from pathlib import Path


USES_LINE = re.compile(r"^\s*(?:-\s*)?uses\s*:\s*(?P<value>.*?)\s*$")
QUOTED_MAPPING_KEY = re.compile(
    r'''^\s*(?:-\s*)?(?:"(?:\\.|[^"\\])*"|'(?:''|[^'])*')\s*:'''
)
SPECIAL_MAPPING_KEY = re.compile(r"^\s*(?:-\s*)?(?:\?(?:\s|$)|[!&*])")
FLOW_MAPPING = re.compile(r"^\s*(?:-\s*)?\{")
NESTED_FLOW_MAPPING = re.compile(r"^\s*[^:#]+:\s*\[[^#]*\{")
FLOW_MAPPING_VALUE = re.compile(
    r"^\s*[^:#]+:\s*(?:(?:!+\S+|&\S+)\s+)*\{(?!\{)"
)
PINNED_ACTION = re.compile(r"^[^@\s]+@[0-9a-f]{40}$")
VERSION_COMMENT = re.compile(r"^#\s+v\d+(?:\.\d+)*(?:[-+][0-9A-Za-z.-]+)?\s*$")


def split_scalar_and_comment(value: str) -> tuple[str, str | None]:
    quote: str | None = None
    escaped = False
    for index, character in enumerate(value):
        if escaped:
            escaped = False
            continue
        if quote == '"' and character == "\\":
            escaped = True
            continue
        if character in {"'", '"'}:
            if quote is None:
                quote = character
            elif quote == character:
                quote = None
            continue
        if character == "#" and quote is None:
            return value[:index].rstrip(), value[index:].strip()
    return value.strip(), None


def unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def find_unpinned_actions(text: str, source: str) -> list[str]:
    errors: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if any(
            pattern.match(line)
            for pattern in (
                QUOTED_MAPPING_KEY,
                SPECIAL_MAPPING_KEY,
                FLOW_MAPPING,
                NESTED_FLOW_MAPPING,
                FLOW_MAPPING_VALUE,
            )
        ):
            errors.append(
                f"{source}:{line_number}: unsupported uses syntax; "
                "use an unquoted block key"
            )
            continue
        match = USES_LINE.match(line)
        if not match:
            continue
        scalar, comment = split_scalar_and_comment(match.group("value"))
        action = unquote(scalar.strip())
        if action.startswith("./") or action.startswith("docker://"):
            continue
        if not PINNED_ACTION.fullmatch(action) or not (
            comment and VERSION_COMMENT.fullmatch(comment)
        ):
            errors.append(
                f"{source}:{line_number}: third-party action must use a "
                "40-character lowercase SHA with a version comment: "
                f"{action}"
            )
    return errors


def validate_workflows(root: Path) -> list[str]:
    workflow_root = root / ".github/workflows"
    paths = sorted(
        {
            *workflow_root.glob("*.yml"),
            *workflow_root.glob("*.yaml"),
        }
    )
    errors: list[str] = []
    for path in paths:
        source = path.relative_to(root).as_posix()
        errors.extend(find_unpinned_actions(path.read_text(encoding="utf-8"), source))
    return errors


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    root = Path(arguments[0]).resolve() if arguments else Path(__file__).parents[1]
    errors = validate_workflows(root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
