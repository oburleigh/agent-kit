# Git Commit

A skill for creating review-ready git commits following Conventional Commits v1.0.0.

## What it does

1. Checks branch protection (refuses to commit on `main`/`master`)
2. Detects project-specific conventions from `docs/commit-conventions.md` if present
3. Runs project prerequisite gates if defined (e.g. test, lint, typecheck)
4. Inspects the working tree and decides commit boundaries
5. Stages files explicitly (no `git add .`, no interactive `git add -p`)
6. Reviews staged changes for secrets, debug code, unrelated churn
7. Writes Conventional Commits messages via HEREDOC (no interactive editors)
8. Respects commitlint hooks and fixes rejected messages instead of bypassing

## Project-aware

The skill automatically loads `docs/commit-conventions.md` from the repo root when it exists. This gives it project-specific:
- Allowed commit types (e.g. `ref` instead of `refactor`)
- Required scopes (e.g. must match package names)
- Subject line length limits
- Prerequisite gates that must pass before committing
- Branch protection rules

When no project conventions exist, it falls back to standard Conventional Commits.

## What it does NOT do

- Push to remote (the user must explicitly ask)
- Run the project's full review chain. Code reviews and other release gates are prerequisites, not part of this skill.
- Create branches or worktrees (use other tools for that)

## Trigger phrases

- "commit this work"
- "create a commit"
- "split these changes into commits"

## References

- `references/examples.md`: house-style commit message examples
- [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
