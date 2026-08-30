---
name: typescript-scaffold
description: Use when creating a new TypeScript or Node.js repository, including libraries, services, CLIs, workspaces, and Vite React applications. Not for retrofitting or regenerating an existing repository.
---

# TypeScript Scaffold

Create a new repository from a reusable profile. Keep the profile outside this skill so agent-kit updates cannot replace user choices.

## Requirements

Require Node.js 24, Git when enabled, the selected package manager, and any external tools selected by the profile, such as Gitleaks. Report missing tools. Do not install global tools or drop configured checks without permission.

## Workflow

1. Resolve the target, project name, description, author, repository URL, preset, requested stack, and initial workspace members. Ask only when an unsafe or material choice cannot be inferred.
2. Select a profile:
   - A path loads that YAML file.
   - `library`, `service`, `cli`, or `workspace` loads the matching persistent profile and creates it from the bundled preset when absent.
   - `<preset>:<profile-name>` creates or loads a named persistent profile.
3. Read the provider fields, compatibility rules, and profile format in [README.md](README.md#provider-fields) when choosing providers or editing a profile.
4. For per-run changes, copy the persistent profile to a temporary YAML file and change only the requested fields. Fill its `project` section. Never write per-run values back unless the user asks to save them.
5. Run the read-only plan with the resolved profile or temporary profile:

   ```sh
   node <skill-directory>/dist/generate.mjs --plan --profile <profile-or-selector> --target <target>
   ```

6. Use the plan JSON as the authoritative pre-generation summary. State the target, resolved stack, disabled providers, initial workspace members, and planned quality gates. A user should not need to know that a profile exists to understand what will be created. Do not reconstruct the plan from generator source or narrate discarded options and scaffold history.
7. Run the same command without `--plan`.
8. After a successful exit, report the created path, selected providers, and checks that passed. Treat the successful deterministic run as the verification evidence. Do not read generator internals, full logs, or every generated file.

## Boundaries

- Create only. Refuse any existing target and never regenerate or update an existing repository.
- Never edit bundled presets. Persistent profiles live in the platform user-config directory and are created only when absent.
- Treat `config/defaults.yaml` as release-owned fallback policy. Put user overrides in persistent profiles.
- Keep profiles and temporary answers out of the generated repository.
- Let first-class providers own their dependencies, files, scripts, hooks, documentation, and CI steps.
- Give every selected tool a portable working configuration with real rules, exclusions, and thresholds. Do not generate empty config files or duplicate rules already supplied by an extended maintained preset.
- Keep tool responsibilities separate. A formatter formats, a linter checks code, a hook runner invokes checks, and a workspace tool orchestrates package tasks.
- Treat generated `AGENTS.md` and `docs/coding-standards.md` as the repository's complete engineering baseline. Do not assume the user has a companion TypeScript skill.
- For workspaces, compose root quality and test tools with the workspace orchestrator. Never replace real checks with empty Turbo or Nx tasks.
- Extra dependencies and scripts are copied as configuration. Do not invent integration code for an unknown package.
- Prefer maintained packages for solved, non-domain work. Write custom infrastructure only when existing packages cannot meet the required contract, then keep it narrow and tested.
- Preserve official framework-generator structure and commands. Apply agent-kit files as an overlay.
- Do not create a remote, push, or make an initial commit unless the user requests it.

If generation fails, use the reported command, bounded failure output, and focused command logs to diagnose it. Inspect only the profile and implementation files implicated by that evidence. Broaden inspection only when the evidence requires it or the user asks for a scaffold review. The generator cleans targets it created and preserves user-owned paths.
