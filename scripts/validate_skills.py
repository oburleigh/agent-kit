#!/usr/bin/env python3
"""Validate repository-specific quality rules for published Agent Skills."""

from __future__ import annotations

import json
import os
import re
import sys
from collections import deque
from pathlib import Path
from urllib.parse import unquote, urlsplit

from skills_ref.errors import ParseError
from skills_ref.parser import parse_frontmatter


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
RESOURCE_DIRECTORIES = ("scripts", "references", "assets")
IGNORED_PARTS = {
    ".coverage",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "htmlcov",
    "node_modules",
}


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _error(skill: Path, message: str) -> str:
    return f"{skill.name}/{message}"


def _frontmatter(skill_file: Path) -> tuple[dict[str, object], list[str]]:
    try:
        metadata, _ = parse_frontmatter(skill_file.read_text(encoding="utf-8"))
    except (ParseError, UnicodeDecodeError) as exc:
        return {}, [str(exc)]
    return metadata, []


def _validate_metadata(skill: Path) -> list[str]:
    skill_file = skill / "SKILL.md"
    if not skill_file.is_file():
        return [_error(skill, "SKILL.md is required")]

    metadata, errors = _frontmatter(skill_file)
    errors = [_error(skill, message) for message in errors]
    name = metadata.get("name", "")
    description = metadata.get("description", "")

    if name != skill.name:
        errors.append(_error(skill, "name does not match directory"))
    if not isinstance(name, str) or not SKILL_NAME.fullmatch(name):
        errors.append(_error(skill, "name is not kebab case"))
    if not isinstance(description, str) or not description.startswith("Use when"):
        errors.append(_error(skill, "description must start with 'Use when'"))
    if isinstance(description, str) and len(description) > 1024:
        errors.append(_error(skill, "description must be at most 1024 characters"))
    if len(skill_file.read_text(encoding="utf-8").splitlines()) >= 500:
        errors.append(_error(skill, "SKILL.md must be under 500 lines"))
    return errors


def _fixture_paths(evaluation: dict[str, object]) -> tuple[list[str], list[str]]:
    paths: list[str] = []
    errors: list[str] = []
    for key in ("files", "fixtures"):
        if key not in evaluation:
            continue
        value = evaluation[key]
        if not isinstance(value, list):
            errors.append(f"{key} must be a list")
            continue
        for item in value:
            if isinstance(item, str):
                paths.append(item)
            elif isinstance(item, dict) and isinstance(item.get("path"), str):
                paths.append(item["path"])
            else:
                errors.append(f"{key} entries must be paths or objects with a path")

    fixture = evaluation.get("fixture")
    if fixture is not None:
        if isinstance(fixture, str):
            paths.append(fixture)
        elif isinstance(fixture, dict) and isinstance(fixture.get("path"), str):
            paths.append(fixture["path"])
        else:
            errors.append("fixture must be a path or an object with a path")
    return paths, errors


def _validate_evals(skill: Path) -> list[str]:
    eval_file = skill / "evals" / "evals.json"
    if not eval_file.is_file():
        return [_error(skill, "evals/evals.json is required")]

    try:
        payload = json.loads(eval_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [_error(skill, f"evals/evals.json is invalid JSON: {exc}")]
    if not isinstance(payload, dict):
        return [_error(skill, "evals/evals.json must contain an object")]

    errors: list[str] = []
    if payload.get("skill_name") != skill.name:
        errors.append(_error(skill, "evals skill_name must match the skill directory"))
    evaluations = payload.get("evals")
    if not isinstance(evaluations, list) or not evaluations:
        errors.append(_error(skill, "evals must be a non-empty list"))
        return errors

    seen_ids: set[str | int] = set()
    for index, evaluation in enumerate(evaluations, start=1):
        prefix = f"evals[{index}]"
        if not isinstance(evaluation, dict):
            errors.append(_error(skill, f"{prefix} must be an object"))
            continue

        eval_id = evaluation.get("id")
        valid_id = isinstance(eval_id, (str, int)) and not isinstance(eval_id, bool)
        if isinstance(eval_id, str):
            valid_id = bool(eval_id.strip())
        if not valid_id:
            errors.append(_error(skill, f"{prefix} id must be a non-empty string or integer"))
        elif eval_id in seen_ids:
            errors.append(_error(skill, "eval IDs must be unique"))
        else:
            seen_ids.add(eval_id)

        for field in ("prompt", "expected_output"):
            value = evaluation.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(_error(skill, f"{prefix} {field} must be non-empty text"))

        assertions = evaluation.get("assertions")
        if not isinstance(assertions, list) or not assertions:
            errors.append(_error(skill, f"{prefix} assertions must be a non-empty list"))
        elif any(not isinstance(item, str) or not item.strip() for item in assertions):
            errors.append(_error(skill, f"{prefix} assertions must contain non-empty text"))

        fixture_paths, fixture_errors = _fixture_paths(evaluation)
        errors.extend(_error(skill, f"{prefix} {message}") for message in fixture_errors)
        for fixture_path in fixture_paths:
            target = (skill / fixture_path).resolve()
            try:
                target.relative_to(skill.resolve())
            except ValueError:
                errors.append(_error(skill, f"{prefix} fixture escapes the skill: {fixture_path}"))
                continue
            if not target.is_file():
                errors.append(_error(skill, f"{prefix} fixture does not exist: {fixture_path}"))
    return errors


def _local_link_target(markdown: Path, raw_target: str) -> Path | None:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    target = target.split(maxsplit=1)[0]
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or target.startswith("#"):
        return None
    path = unquote(parsed.path)
    if not path:
        return None
    return (markdown.parent / path).resolve()


def _markdown_links(path: Path) -> list[Path]:
    text = path.read_text(encoding="utf-8")
    return [
        target
        for match in MARKDOWN_LINK.finditer(text)
        if (target := _local_link_target(path, match.group(1))) is not None
    ]


def _validate_markdown_links(skill: Path) -> list[str]:
    errors: list[str] = []
    root = skill.resolve()
    for markdown in skill.rglob("*.md"):
        if IGNORED_PARTS.intersection(markdown.relative_to(skill).parts):
            continue
        for target in _markdown_links(markdown):
            try:
                target.relative_to(root)
            except ValueError:
                errors.append(
                    _error(
                        skill,
                        f"broken local link in {_relative(markdown, skill)}: target escapes the skill",
                    )
                )
                continue
            if not target.exists():
                errors.append(
                    _error(
                        skill,
                        f"broken local link in {_relative(markdown, skill)}: {_relative(target, skill)}",
                    )
                )
    return errors


def _resource_files(skill: Path) -> list[Path]:
    resources: list[Path] = []
    for directory_name in RESOURCE_DIRECTORIES:
        directory = skill / directory_name
        if not directory.is_dir():
            continue
        resources.extend(
            path
            for path in directory.rglob("*")
            if (path.is_file() or path.is_symlink())
            and not IGNORED_PARTS.intersection(path.relative_to(skill).parts)
        )
    return sorted(resources)


def _mentions_path(text: str, path: str) -> bool:
    return re.search(
        rf"(?<![A-Za-z0-9_./-]){re.escape(path)}"
        rf"(?!(?:[A-Za-z0-9_/-]|\.[A-Za-z0-9_]))",
        text,
    ) is not None


def _referenced_resources(skill: Path, resources: list[Path]) -> set[Path]:
    roots = [skill / "SKILL.md", skill / "evals" / "evals.json"]
    queue = deque(path.resolve() for path in roots if path.is_file())
    visited: set[Path] = set()
    referenced: set[Path] = set()
    skill_root = skill.resolve()
    resource_set = set(resources)

    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        try:
            text = current.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        if current.suffix.lower() == ".md":
            for target in _markdown_links(current):
                if target.is_file() and target.is_relative_to(skill_root):
                    queue.append(target)

        for resource in resource_set:
            root_relative = resource.relative_to(skill_root).as_posix()
            current_relative = Path(os.path.relpath(resource, current.parent)).as_posix()
            if _mentions_path(text, root_relative) or _mentions_path(text, current_relative):
                if resource not in referenced:
                    referenced.add(resource)
                    queue.append(resource)
    return referenced


def _validate_resource_reachability(skill: Path) -> list[str]:
    resources = _resource_files(skill)
    skill_root = skill.resolve()
    valid_resources: list[Path] = []
    errors: list[str] = []
    for resource in resources:
        resolved = resource.resolve()
        try:
            resolved.relative_to(skill_root)
        except ValueError:
            errors.append(
                _error(skill, f"resource escapes the skill: {_relative(resource, skill)}")
            )
            continue
        if not resolved.is_file():
            errors.append(
                _error(skill, f"resource target does not exist: {_relative(resource, skill)}")
            )
            continue
        valid_resources.append(resource)

    referenced = _referenced_resources(skill, valid_resources)
    errors.extend(
        _error(skill, f"unreachable resource: {_relative(resource, skill)}")
        for resource in valid_resources
        if resource not in referenced
    )
    return errors


def validate_skill(skill: Path) -> list[str]:
    return [
        *_validate_metadata(skill),
        *_validate_evals(skill),
        *_validate_markdown_links(skill),
        *_validate_resource_reachability(skill),
    ]


def validate_repository(root: Path = ROOT) -> list[str]:
    skills = root / "skills"
    if not skills.is_dir():
        return ["skills directory is required"]
    errors: list[str] = []
    for skill in sorted(path for path in skills.iterdir() if (path / "SKILL.md").is_file()):
        errors.extend(validate_skill(skill))
    return errors


def main() -> int:
    errors = validate_repository()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    count = sum(1 for path in (ROOT / "skills").iterdir() if (path / "SKILL.md").is_file())
    print(f"Validated {count} published skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
