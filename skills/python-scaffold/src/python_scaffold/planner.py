from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from python_scaffold.paths import require_normalized_relative_path


class PlanningError(ValueError):
    pass


@dataclass(frozen=True)
class Contribution:
    provider: str
    dependencies: tuple[str, ...] = ()
    dev_dependencies: tuple[str, ...] = ()
    files: Mapping[str, str] = field(default_factory=dict)
    commands: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    gates: tuple[tuple[str, ...], ...] = ()
    responsibilities: tuple[str, ...] = ()


@dataclass(frozen=True)
class Plan:
    dependencies: tuple[str, ...]
    dev_dependencies: tuple[str, ...]
    files: Mapping[str, str]
    commands: Mapping[str, tuple[str, ...]]
    gates: tuple[tuple[str, ...], ...]


def compose(contributions: Iterable[Contribution]) -> Plan:
    dependencies: dict[str, tuple[str, str]] = {}
    dev_dependencies: dict[str, tuple[str, str]] = {}
    dependency_groups: dict[str, tuple[str, str]] = {}
    files: dict[str, tuple[str, str]] = {}
    commands: dict[str, tuple[str, tuple[str, ...]]] = {}
    responsibilities: dict[str, tuple[str, None]] = {}
    gates: list[tuple[str, ...]] = []

    for contribution in contributions:
        _add_requirements(
            dependencies,
            dependency_groups,
            contribution.dependencies,
            contribution.provider,
            "runtime",
        )
        _add_requirements(
            dev_dependencies,
            dependency_groups,
            contribution.dev_dependencies,
            contribution.provider,
            "development",
        )
        _add_files(files, contribution.files, contribution.provider)
        _claim_entries(commands, contribution.commands, contribution.provider, "command")
        gates.extend(contribution.gates)
        for responsibility in contribution.responsibilities:
            _claim_entry(
                responsibilities,
                responsibility,
                None,
                contribution.provider,
                "responsibility",
            )

    return Plan(
        dependencies=tuple(sorted(value[1] for value in dependencies.values())),
        dev_dependencies=tuple(sorted(value[1] for value in dev_dependencies.values())),
        files=MappingProxyType({path: value for path, (_, value) in sorted(files.items())}),
        commands=MappingProxyType({name: value for name, (_, value) in sorted(commands.items())}),
        gates=tuple(gates),
    )


def _add_requirements(
    destination: dict[str, tuple[str, str]],
    groups: dict[str, tuple[str, str]],
    requirements: Iterable[str],
    provider: str,
    group: str,
) -> None:
    for raw in requirements:
        requirement = Requirement(raw)
        name = canonicalize_name(requirement.name)
        normalized = str(requirement)
        existing_group = groups.get(name)
        if existing_group is not None and existing_group[0] != group:
            raise PlanningError(
                f"Provider {provider} conflicts with {existing_group[1]} on dependency {name}"
            )
        existing = destination.get(name)
        if existing is not None and existing[1] != normalized:
            raise PlanningError(
                f"Provider {provider} conflicts with {existing[0]} on dependency {name}"
            )
        destination[name] = (provider, normalized)
        groups[name] = (group, provider)


def _add_files(
    destination: dict[str, tuple[str, str]], values: Mapping[str, str], provider: str
) -> None:
    try:
        normalized = {
            require_normalized_relative_path(path): value for path, value in values.items()
        }
    except ValueError as error:
        raise PlanningError(f"Provider {provider}: {error}") from error
    _claim_entries(destination, normalized, provider, "file path")


def _claim_entries[T](
    destination: dict[str, tuple[str, T]],
    values: Mapping[str, T],
    provider: str,
    kind: str,
) -> None:
    for name, value in values.items():
        _claim_entry(destination, name, value, provider, kind)


def _claim_entry[T](
    destination: dict[str, tuple[str, T]], name: str, value: T, provider: str, kind: str
) -> None:
    existing = destination.get(name)
    if existing is not None:
        raise PlanningError(f"Provider {provider} conflicts with {existing[0]} on {kind} {name}")
    destination[name] = (provider, value)
