# Commit message examples

House-style examples for Conventional Commits v1.0.0. Match the voice, body length, and specificity shown below — concise bodies that explain *why*, not essays.

## Format

```
<type>[(scope)][!]: <imperative summary>

[body: what changed and why, wrapped at 100 chars]

[footer(s): Fixes #N | Refs #N | BREAKING CHANGE: ...]
```

## Feature

```
feat(core): Add task packet schema with Zod validation

Define TaskPacket interface and Zod schema covering all required
fields. Runtime validation rejects malformed packets at the
system boundary before any processing begins.
```

## Bug fix with issue reference

```
fix(temporal): Handle signal race during state transition

Workflow could receive a clarification signal while mid-transition,
causing the state machine to enter an invalid state. Buffer signals
until the current transition completes.

Fixes #42
```

## Breaking change

```
feat(api)!: Replace REST intake with webhook-based triggers

The /api/v1/tasks POST endpoint is removed. All task intake now
arrives via registered webhooks from Slack, Jira, or Notion.

BREAKING CHANGE: REST intake endpoint removed. All clients must
migrate to webhook-based triggers.

Refs #89
```

## Refactor

```
refactor(auth): Extract token validation into shared middleware

Three handlers duplicated the same JWT verify + claim-check logic.
Consolidate into authMiddleware so changes land in one place.
No behavior change.
```

## Test

```
test(sandbox): Add gVisor boot integration tests

Verify container boots within 5s, runs commands, and cleans up on
teardown. Falls back to standard Docker runtime when gVisor is
unavailable in CI.
```

## Chore

```
chore(deps): Bump zod from 3.22.4 to 3.23.8

Patch release — no schema API changes affecting this codebase.
```
