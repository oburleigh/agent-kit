---
name: python-scaffold
description: Use when creating a new Python repository, including libraries, services, command-line applications, and uv workspaces. Not for retrofitting or regenerating an existing repository.
---

# Python Scaffold

Create a new repository from a reusable profile. Profiles live outside the installed skill, so Agent Kit updates do not overwrite user choices.

## Workflow

1. Resolve the target, preset, project name, description, author, repository URL, Python version, provider choices, and workspace members. Ask only when a material choice cannot be inferred safely.
2. Select `library`, `service`, `cli`, or `workspace`. Use `<preset>:<profile-name>` for a named persistent profile, or pass a YAML path.
3. Read [README.md](README.md#provider-fields) before changing providers. Enforce the documented compatibility rules and keep actual product choices alphabetical, with `none` last.
4. Use a temporary YAML copy for per-run provider changes. Never write those changes back to a persistent profile unless the user asks to save them.
5. Run the read-only plan with the resolved profile or temporary profile:

   ```sh
   uv run --project <skill-directory> python-scaffold --plan \
     --profile <profile-or-path> \
     --target <target> \
     --name <project-name> \
     --description <description> \
     --author <author>
   ```

6. Use the plan JSON as the authoritative pre-generation summary. State the target, resolved stack, disabled providers, workspace members, and planned quality gates. Do not reconstruct the plan from generator source.
7. Run the same command without `--plan`.
8. After a successful exit, report the created path, selected providers, and checks that passed. Treat the successful deterministic run as the verification evidence. Do not read generator internals, full logs, or every generated file.

## Boundaries

- Create only. Refuse existing targets and never regenerate or update a repository.
- Keep persistent profiles in the platform user-config directory. Treat bundled presets and package versions as release-owned defaults.
- Use maintained packages for solved, non-domain work. Add custom infrastructure only when no maintained package meets the required contract.
- Give each selected tool usable rules, thresholds, exclusions, commands, hooks, CI steps, and documentation. Do not configure two tools for the same responsibility.
- Keep Ruff responsible for formatting and general linting. When selected, Pylint checks duplication only.
- Keep generated `AGENTS.md` and `docs/coding-standards.md` self-contained. Do not assume another Python skill is installed.
- Write comments only for intent, constraints, or non-obvious trade-offs. Do not narrate code or record change history in comments.
- Do not create a remote, push, or make an initial commit unless the user requests it.

If dependency installation or a selected gate fails, use the reported command, bounded failure output, and focused command logs to diagnose it. Inspect only the profile and implementation files implicated by that evidence. Broaden inspection only when the evidence requires it or the user asks for a scaffold review. The generator removes its staging directory and preserves user-owned paths.
