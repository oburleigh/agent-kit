from pathlib import Path
from typing import Annotated

import typer

from python_scaffold.generate import generate_repository
from python_scaffold.profiles import resolve_profile

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.command()
def create(
    profile: Annotated[str, typer.Option("--profile")],
    target: Annotated[Path, typer.Option("--target")],
    name: Annotated[str | None, typer.Option("--name")] = None,
    description: Annotated[str | None, typer.Option("--description")] = None,
    author: Annotated[str | None, typer.Option("--author")] = None,
    repository_url: Annotated[str | None, typer.Option("--repository-url")] = None,
    install: Annotated[bool, typer.Option("--install/--no-install")] = True,
    check: Annotated[bool, typer.Option("--check/--no-check")] = True,
    git: Annotated[bool, typer.Option("--git/--no-git")] = True,
) -> None:
    project_overrides = {
        key: value
        for key, value in {
            "name": name,
            "description": description,
            "author": author,
            "repository_url": repository_url,
        }.items()
        if value is not None
    }
    resolved = resolve_profile(
        profile,
        overrides={
            "project": project_overrides,
            "execution": {
                "install_dependencies": install,
                "run_quality_gates": check,
                "initialize_git": git,
            },
        },
    )
    created = generate_repository(resolved, target)
    typer.echo(f"Created {created}")
