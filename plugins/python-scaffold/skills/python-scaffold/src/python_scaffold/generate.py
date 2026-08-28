import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from python_scaffold.models import Profile
from python_scaffold.providers import build_plan
from python_scaffold.render import render_repository
from python_scaffold.transaction import create_only

CommandRunner = Callable[[tuple[str, ...], Path], None]


def generate_repository(
    profile_data: Profile | Mapping[str, Any],
    target: Path,
    *,
    run_command: CommandRunner | None = None,
) -> Path:
    raw = (
        profile_data.model_dump(warnings="none")
        if isinstance(profile_data, Profile)
        else profile_data
    )
    profile = Profile.model_validate(raw)
    plan = build_plan(profile)
    runner = run_command or _run

    def build(staging: Path) -> None:
        render_repository(profile, plan, staging)
        if profile.execution.install_dependencies:
            runner(("uv", "sync", "--all-groups"), staging)
        if profile.execution.run_quality_gates:
            for command in plan.gates:
                runner(command, staging)
        if profile.execution.initialize_git:
            runner(("git", "init", "--initial-branch=main"), staging)
            if profile.execution.install_dependencies and profile.providers.hooks == "pre-commit":
                runner(
                    (
                        "uv",
                        "run",
                        "pre-commit",
                        "install",
                        "--hook-type",
                        "pre-commit",
                        "--hook-type",
                        "commit-msg",
                        "--hook-type",
                        "pre-push",
                    ),
                    staging,
                )
            if profile.providers.hooks == "lefthook":
                runner(("lefthook", "install"), staging)

    return create_only(target, build)


def _run(command: tuple[str, ...], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)
