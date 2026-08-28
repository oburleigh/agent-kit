from importlib.resources import files
from pathlib import Path

import tomlkit

from python_scaffold.models import Profile
from python_scaffold.planner import Plan


def render_repository(profile: Profile, plan: Plan, target: Path) -> None:
    files = {**plan.files, "pyproject.toml": _pyproject(profile, plan)}
    license_text = _license_text(profile.providers.license, profile.project.author)
    if license_text is not None:
        files["LICENSE"] = license_text

    for relative_path, content in files.items():
        destination = target / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")


def _pyproject(profile: Profile, plan: Plan) -> str:
    module = profile.project.name.replace("-", "_").replace(".", "_")
    coverage_source = ["apps", "packages"] if profile.preset == "workspace" else ["src"]
    document = tomlkit.document()
    project: dict[str, object] = {
        "name": profile.project.name,
        "version": "0.1.0",
        "description": profile.project.description,
        "readme": "README.md",
        "requires-python": f">={profile.project.python_version}",
        "authors": [{"name": profile.project.author}],
        "dependencies": list(plan.dependencies),
    }
    if profile.providers.license != "none":
        project["license"] = {
            "apache-2.0": "Apache-2.0",
            "mit": "MIT",
        }[profile.providers.license]
    if profile.preset == "cli":
        project["scripts"] = {profile.project.name: f"{module}.cli:app"}
    document["project"] = project
    document["dependency-groups"] = {"dev": list(plan.dev_dependencies)}
    if profile.preset != "workspace":
        document["build-system"] = _build_system(profile.providers.build_backend)
    if profile.providers.build_backend == "uv-build":
        document["tool"] = {
            "uv": {
                **(
                    {"package": False, "workspace": {"members": profile.project.workspace_members}}
                    if profile.preset == "workspace"
                    else {"build-backend": {"module-name": module, "module-root": "src"}}
                )
            },
            "agent-kit": {
                "commands": {name: list(command) for name, command in plan.commands.items()}
            },
            "coverage": {
                "run": {"branch": True, "source": coverage_source},
                "report": {"fail_under": profile.tools.coverage_floor, "show_missing": True},
            },
        }
    else:
        document["tool"] = {
            "agent-kit": {
                "commands": {name: list(command) for name, command in plan.commands.items()}
            },
            "coverage": {
                "run": {"branch": True, "source": coverage_source},
                "report": {"fail_under": profile.tools.coverage_floor, "show_missing": True},
            },
        }
    return tomlkit.dumps(document)


def _build_system(provider: str) -> dict[str, object]:
    systems: dict[str, dict[str, object]] = {
        "hatchling": {"requires": ["hatchling>=1.28,<2"], "build-backend": "hatchling.build"},
        "setuptools": {
            "requires": ["setuptools>=80,<81"],
            "build-backend": "setuptools.build_meta",
        },
        "uv-build": {"requires": ["uv_build>=0.12,<0.13"], "build-backend": "uv_build"},
    }
    return systems[provider]


def _license_text(provider: str, author: str) -> str | None:
    if provider == "none":
        return None
    if provider == "mit":
        return f"""MIT License

Copyright (c) {author}

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
    resource = files("python_scaffold") / "templates/APACHE-2.0.txt"
    return resource.read_text(encoding="utf-8")
