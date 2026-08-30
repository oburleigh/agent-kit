import shlex
from pathlib import Path
from typing import Any

from python_scaffold.models import Profile
from python_scaffold.providers import build_plan


def create_plan_summary(profile: Profile, target: Path) -> dict[str, Any]:
    plan = build_plan(profile)
    providers = profile.providers.model_dump()
    selected = {name: value for name, value in providers.items() if value != "none"}
    disabled = [name for name, value in providers.items() if value == "none"]
    project = profile.project.model_dump(exclude={"workspace_members"})

    return {
        "schema_version": 1,
        "target": str(target.resolve()),
        "preset": profile.preset,
        "project": project,
        "selected_providers": selected,
        "disabled_providers": disabled,
        "workspace_members": profile.project.workspace_members,
        "quality_gates": [shlex.join(command) for command in plan.gates],
        "execution": profile.execution.model_dump(),
    }
