<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/agent-kit-logo-dark.png">
    <source media="(prefers-color-scheme: light)" srcset="assets/agent-kit-logo-light.png">
    <img src="assets/agent-kit-logo-light.png" alt="Agent Kit logo" width="384" height="256">
  </picture>
</p>

Reusable skills for software engineering work with Codex and Claude Code.

The skills are small enough to use independently and work together without imposing a single development process. Install Agent Kit to get the complete set, or install individual skills when you only need part of it.

## Skills

| Skill | What it does |
| --- | --- |
| [create-skill](skills/create-skill/) | Turns a repeatable workflow into a focused Agent Skill, with validation and supporting references where needed. |
| [git-commit](skills/git-commit/) | Reviews the working tree, stages only the intended changes, splits unrelated work, and writes Conventional Commits. |
| [humanize](skills/humanize/) | Edits professional prose to remove common machine-written patterns while preserving the author's meaning and voice. |
| [python-scaffold](skills/python-scaffold/) | Creates configurable Python libraries, services, CLIs, and uv workspaces with working project tooling. |
| [typescript-scaffold](skills/typescript-scaffold/) | Creates configurable TypeScript libraries, services, CLIs, React applications, and monorepos with working project tooling. |

Each skill has its own README with usage details and examples.

## Invocation

All current skills support automatic and explicit invocation. Codex or Claude Code can select a skill when a request matches its description, or you can name it directly:

```text
# Codex
$agent-kit:typescript-scaffold create a TypeScript service

# Claude Code with the complete plugin
/agent-kit:typescript-scaffold create a TypeScript service
```

Selecting a skill loads its instructions. It does not grant permission for unrelated changes or external actions.

## Install the complete plugin

### Codex

```sh
codex plugin marketplace add oburleigh/agent-kit
codex plugin add agent-kit@agent-kit
```

Start a new Codex session after installation.

### Claude Code

```sh
claude plugin marketplace add oburleigh/agent-kit
claude plugin install agent-kit@agent-kit
```

Run `/reload-plugins` or start a new Claude Code session after installation. Add `--scope project` to both Claude commands when a repository should declare the marketplace and plugin for its contributors.

## Install individual skills

The marketplace also publishes each skill as a separate plugin. Add the marketplace using the command above, then install the skill you want:

```sh
# Codex
codex plugin add git-commit@agent-kit

# Claude Code
claude plugin install git-commit@agent-kit
```

Choose either the complete `agent-kit` plugin or individual skill plugins. Installing both loads duplicate copies of the same skills.

## Updates

Update the marketplace before updating an installed plugin.

For Codex:

```sh
codex plugin marketplace upgrade agent-kit
codex plugin remove agent-kit@agent-kit
codex plugin add agent-kit@agent-kit
```

For Claude Code:

```sh
claude plugin marketplace update agent-kit
claude plugin update agent-kit@agent-kit
```

## Repository layout

- The repository root is the complete `agent-kit` plugin.
- `skills/<skill>/` is the canonical source for each skill.
- The root plugin manifests point directly to the canonical skills.
- `plugins/<skill>/` contains generated standalone packages for subset installation. Run `python3 scripts/sync_plugin_skills.py` after changing a canonical skill.
- `.agents/plugins/marketplace.json` is the Codex marketplace catalogue.
- `.claude-plugin/marketplace.json` is the Claude Code marketplace catalogue.
- `tests/` checks that both catalogues publish the same plugins and that the complete plugin stays in sync.

## Local development

Clone the repository and add the checkout as a marketplace source:

```sh
git clone https://github.com/oburleigh/agent-kit.git
codex plugin marketplace add ./agent-kit
claude plugin marketplace add ./agent-kit
```

Run the distribution checks before publishing changes:

```sh
python3 scripts/validate_releases.py
python3 scripts/check_github_actions.py
python3 -m unittest discover -s tests -v
claude plugin validate .
```

## Releases

Each installable plugin has its own version and changelog. A change to one standalone plugin does not bump any other standalone plugin. The complete `agent-kit` plugin may also receive a release because it contains every published skill.

Release Please derives versions from Conventional Commits. Before `1.0.0`, fixes and compatible features produce patch releases, while breaking changes produce minor releases. Starting at `1.0.0`, features produce minor releases and breaking changes produce major releases.

Merges to `main` create or update one reviewable release pull request. They do not create tags or GitHub Releases. Merging the release pull request creates a tag and GitHub Release for each component included in that pull request, using names such as `typescript-scaffold-v0.2.0`.

Repository settings allow GitHub Actions to create the release pull request while keeping the default token read-only. The `main` ruleset requires one approval and the `Plugin distribution`, `Python scaffold`, and `TypeScript scaffold` checks. The distribution check includes runtime manifest validation and clean aggregate and subset installation tests.

## Contributing

Keep skills focused and usable on their own. Put agent instructions in `SKILL.md`, detailed material in `references/`, executable helpers in `scripts/`, and generated-file templates in `assets/`. Run the skill tests and both runtime validators before opening a pull request.

## Licence

[MIT](LICENSE)
