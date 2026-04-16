# Commit message templates (Conventional Commits v1.0.0)

## Standard format

```
<type>(<scope>): <summary>

<What changed.>
<Why it changed.>

<footer(s)>
```

## Types

| Type | When to use |
|------|-------------|
| `feat` | New feature (correlates with MINOR in semver) |
| `fix` | Bug fix (correlates with PATCH in semver) |
| `docs` | Documentation only |
| `test` | Adding or correcting tests |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `perf` | Performance improvement |
| `build` | Build system or external dependencies |
| `ci` | CI configuration |
| `chore` | Maintenance tasks, tooling |

**Note:** Projects may define additional or renamed types (e.g. `ref` instead of `refactor`). Check `docs/commit-conventions.md` in the repo if it exists.

## Subject line

- Imperative mood: "Add feature" not "Added feature"
- First word capitalized
- No period at end
- Max 70 characters (or per project convention)

## Body

- Explain **what** and **why**, not how
- Wrap lines at 100 characters
- Separate from subject with one blank line

## Footers

```
Fixes #1234          — closes the issue when merged
Refs #1234           — links without closing
BREAKING CHANGE: description of what breaks
```

## Breaking changes

Two ways to indicate:
1. `!` in header: `feat(api)!: remove deprecated endpoint`
2. Footer: `BREAKING CHANGE: the /v1/users endpoint has been removed`

Both may be used together. If `!` is present, the `BREAKING CHANGE:` footer MAY be omitted.

## Examples

### Feature

```
feat(core): Add task packet schema with Zod validation

Define TaskPacket interface and Zod schema covering all required
fields. Runtime validation rejects malformed packets at the
system boundary before any processing begins.
```

### Bug fix with issue reference

```
fix(temporal): Handle signal race during state transition

Workflow could receive a clarification signal while mid-transition,
causing the state machine to enter an invalid state. Buffer signals
until the current transition completes.

Fixes #42
```

### Breaking change

```
feat(api)!: Replace REST intake with webhook-based triggers

The /api/v1/tasks POST endpoint is removed. All task intake now
arrives via registered webhooks from Slack, Jira, or Notion.

BREAKING CHANGE: REST intake endpoint removed. All clients must
migrate to webhook-based triggers.

Refs #89
```

### Test

```
test(sandbox): Add gVisor boot integration tests

Verify container boots within 5s, runs commands, and cleans up on
teardown. Falls back to standard Docker runtime when gVisor is
unavailable in CI.
```
