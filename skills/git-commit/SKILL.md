---
name: git-commit
description: "Create high-quality git commits: review and stage intended changes, split into logical commits, and write clear commit messages following Conventional Commits v1.0.0. Use when the user asks to commit, save their work, craft a commit message, stage changes, or split work into multiple commits. Also use when the user says they're done with a task or wants to checkpoint progress, even if they don't explicitly say 'commit'."
compatibility: Requires git
---

# Git commit

## Goal

Make commits that are easy to review and safe to ship:
- only intended changes are included
- commits are logically scoped (split when needed)
- commit messages follow Conventional Commits v1.0.0 exactly
- project-specific conventions are detected and enforced

## Conventional Commits specification (v1.0.0)

Every commit message MUST follow this format:

```
<type>[optional scope][optional !]: <description>

[optional body]

[optional footer(s)]
```

Rules (from conventionalcommits.org/en/v1.0.0):
1. Commits MUST be prefixed with a type (`feat`, `fix`, etc.), followed by OPTIONAL scope, OPTIONAL `!`, and REQUIRED terminal colon and space.
2. `feat` MUST be used when a commit adds a new feature.
3. `fix` MUST be used when a commit represents a bug fix.
4. A scope MAY be provided after the type — a noun describing a section of the codebase in parentheses, e.g. `fix(parser):`.
5. A description MUST immediately follow the colon and space. It is a short summary in imperative mood.
6. A longer body MAY follow after one blank line. Free-form, any number of paragraphs.
7. One or more footers MAY follow after one blank line. Each footer is a `token: value` or `token #value` pair.
8. Breaking changes MUST be indicated by `!` before the `:` in the header, and/or by a `BREAKING CHANGE:` footer.
9. Types other than `feat` and `fix` MAY be used (e.g. `docs`, `test`, `chore`, `refactor`, `perf`, `build`, `ci`).

## Project-aware conventions

Before starting, check for project-specific commit conventions:

1. Look for `docs/commit-conventions.md` in the repo root
2. If it exists, load it and treat it as authoritative for:
   - Allowed types (the project may add or rename types, e.g. `ref` instead of `refactor`)
   - Required scopes (the project may mandate scopes matching package names)
   - Subject line length limits
   - Prerequisites that must pass before committing (test gates, reviews)
   - Branch protection rules (e.g. never commit to `main`)
3. If it does not exist, fall back to the Conventional Commits spec above with no project-specific constraints.
4. Also check AI assistant config files for commit-related rules (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `.cursor/rules`, or equivalent for your platform).

## Workflow

### 0. Pre-flight checks

- Run `git branch --show-current` — if on a protected branch (e.g. `main`, `master`), STOP and tell the user. Do not commit.
- If project conventions define prerequisite gates (e.g. `pnpm test && pnpm lint && pnpm typecheck`), verify they have been run and passed in this session. If not, run them now. All must exit 0 before proceeding.

### 1. Inspect the working tree

```bash
git status
git diff --stat
git diff          # unstaged changes
git diff --cached # already staged changes
```

Understand the full scope of what changed before deciding how to commit.

### 2. Decide commit boundaries

Split into multiple commits when changes are unrelated:
- Feature vs refactor
- Backend vs frontend
- Formatting vs logic
- Tests vs production code
- Dependency bumps vs behavior changes
- Docs vs code

Default to multiple small commits when changes span unrelated concerns. Default to a single commit when all changes serve one purpose.

### 3. Stage selectively

Stage files explicitly by name:

```bash
git add src/specific-file.ts src/other-file.ts
```

**Do NOT use `git add .` or `git add -A`** — these can accidentally include secrets, debug files, or unrelated changes.

**Do NOT use `git add -p`** (interactive patch mode) — this requires interactive input that is not supported. If a single file contains changes for multiple commits, stage the file in the commit where the majority of its changes belong, or restructure the approach.

### 4. Review what will be committed

```bash
git diff --cached
```

Check for:
- Secrets, tokens, or credentials (`.env` values, API keys)
- Accidental debug logging (`console.log`, `debugger`)
- Unrelated formatting churn
- Files that don't belong in this commit

If any issues found, unstage with `git restore --staged <path>` and fix.

### 5. Describe the change (think before writing)

In 1-2 sentences, articulate:
- **What** changed?
- **Why** did it change?

If you cannot describe it cleanly, the commit is too big or mixed — go back to step 2.

### 6. Write the commit message

Use a HEREDOC for multi-line messages:

```bash
git commit -m "$(cat <<'EOF'
type(scope): short imperative summary

What changed and why. Explain motivation and contrast with
previous behavior when relevant. Do not describe implementation
details — the diff shows the how.

Refs #1234
EOF
)"
```

Rules for the message:
- Subject line: imperative mood ("Add", "Fix", "Remove"), max 70 chars (or per project convention), no period at end
- Type and scope: per project conventions, or standard Conventional Commits types
- Body: explain what and why, not how. Wrap at 100 chars.
- Footer: `Fixes #N` closes an issue, `Refs #N` links without closing. `BREAKING CHANGE:` for breaking changes.
- **No Co-Authored-By footers** unless the user explicitly requests one.

### 7. Verify after committing

If the commit succeeds, run `git log --oneline -3` to confirm the message looks right.

If a commitlint hook rejects the commit:
- Read the error message
- Fix the commit message format
- Create a NEW commit (do not use `--amend` unless the user asks — amending can destroy the previous commit's work)
- **Never use `--no-verify`** to bypass hooks

### 8. Repeat

If there are remaining uncommitted changes that belong in a separate commit, repeat from step 3 until the working tree is clean or only unrelated changes remain.

## What this skill does NOT do

- It does not push to remote — the user must explicitly ask for that.
- It does not run the project's full review chain (e.g. Codex reviews) — those are prerequisites that should happen before invoking this skill.
- It does not create branches or worktrees — use other tools for that.

## Deliverable

After committing, provide:
- The commit hash and message for each commit created
- A one-line summary of what each commit contains
- Confirmation that any project-specific gates passed
