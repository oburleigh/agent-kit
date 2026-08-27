---
name: git-commit
description: "Use when the user explicitly asks to commit, save, stage, checkpoint, split changes, or write a Git commit message."
compatibility: Requires git
---

# Git commit

## Goal

Commits that are easy to review and safe to ship: only intended changes, logically scoped, Conventional Commits v1.0.0 format, project conventions respected.

## Project conventions

Before committing, check for project-specific rules in this order:

1. `docs/commit-conventions.md`: authoritative if present (may override allowed types, required scopes, subject length, test gates, or branch protection)
2. AI assistant config files for commit rules: `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `.cursor/rules`
3. Otherwise, standard Conventional Commits v1.0.0

## Workflow

### 0. Pre-flight

- Run `git branch --show-current`. If on `main`/`master` or another protected branch, STOP and tell the user.
- If project defines prerequisite gates (tests, lint, typecheck), they must have passed in this session. Run them if not; all must exit 0.

### 1. Inspect

Run `git status`, `git diff`, `git diff --cached`. Understand the full scope before deciding how to commit.

### 2. Decide boundaries

Split into multiple commits when changes are unrelated: feature vs refactor, backend vs frontend, formatting vs logic, tests vs code, deps vs behavior, docs vs code. One commit when all changes serve one purpose.

### 3. Stage selectively

Stage files explicitly by name: `git add src/foo.ts src/bar.ts`.

- **Never `git add .` or `git add -A`**: pulls in secrets, debug files, and unrelated changes.
- **Never `git add -p`**: requires interactive input. If one file spans multiple commits, stage it with the majority of its changes.

### 4. Review staged changes

Run `git diff --cached`. Check for:

- Secrets, tokens, credentials
- Debug output (`console.log`, `debugger`)
- Unrelated formatting churn
- Wrong-scope files

Unstage issues with `git restore --staged <path>` before committing.

### 5. Write the message

Conventional Commits v1.0.0 format:

```
<type>[(scope)][!]: <imperative summary>

[body: what changed and why, not how. Wrap at 100 chars.]

[footer(s): Fixes #N | Refs #N | BREAKING CHANGE: ...]
```

- Subject: imperative mood, max 70 chars (or project override), no trailing period
- Body: explain the why and contrast with previous behavior; the diff shows the how
- Use `!` before `:` or a `BREAKING CHANGE:` footer for breaking changes
- **No `Co-Authored-By` unless the user explicitly asks**

Use HEREDOC for multi-line:

```bash
git commit -m "$(cat <<'EOF'
type(scope): imperative summary

Explain what and why.

Refs #1234
EOF
)"
```

### 6. Verify

`git log --oneline -3` to confirm.

If a hook rejects the commit:

- Read the error, fix the message
- Create a NEW commit. **Never `--amend` unless the user asks** (amending can destroy the previous commit's work).
- **Never `--no-verify`**

### 7. Repeat

If uncommitted changes remain that belong in a separate commit, loop from step 3.
