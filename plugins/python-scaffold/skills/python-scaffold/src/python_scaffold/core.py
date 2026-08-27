from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, Protocol

from python_scaffold.models import Profile
from python_scaffold.planner import Contribution, Plan, compose
from python_scaffold.transaction import create_only


class Renderer(Protocol):
    def __call__(self, profile: Profile, plan: Plan, staging: Path) -> None: ...


def generate_repository(
    profile_data: Profile | Mapping[str, Any],
    target: Path,
    contributions: Iterable[Contribution],
    render: Renderer,
) -> Path:
    raw_profile = (
        profile_data.model_dump(warnings="none")
        if isinstance(profile_data, Profile)
        else profile_data
    )
    profile = Profile.model_validate(raw_profile)
    plan = compose(contributions)
    return create_only(target, lambda staging: render(profile, plan, staging))
