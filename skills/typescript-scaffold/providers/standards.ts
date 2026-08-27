import type { ProviderContribution, ProviderContext } from "../src/types.js";

export const standardsProvider: ProviderContribution = {
  id: "standards",
  selected: () => true,
  files: (context) => ({
    "AGENTS.md": agentsInstructions(context),
    "docs/coding-standards.md": codingStandards(context),
  }),
};

function agentsInstructions(context: ProviderContext): string {
  const commands = completionCommands(context);
  const architecture = context.profile.preset === "workspace"
    ? "Applications belong under `apps/`; shared libraries belong under `packages/`. Keep package entry points small and make dependencies point from applications to libraries."
    : "Keep domain and library code independent of process entry points, environment access, logging setup, and transport adapters. Pass typed dependencies across those boundaries.";
  const testing = context.profile.tests === "none"
    ? "This profile has no test runner. Add and configure one before introducing behavior that needs automated verification."
    : `Use ${testRunnerName(context.profile.tests)} for behavior and public-contract tests. Add a failing test before fixing a defect or adding behavior.`;
  const commits = context.profile.commit_lint === "commitlint"
    ? "Commit messages must follow Conventional Commits. Commitlint enforces the format through the configured Git hook."
    : "Use focused commit messages that explain the delivered change.";

  return `# Working in this repository

Read [docs/coding-standards.md](docs/coding-standards.md) before changing code. Automated rules belong in the compiler, formatter, linter, tests, hooks, or repository checks. Review covers judgment that those tools cannot express.

## Reuse and dependencies

Search the owning package, the full workspace, installed dependencies, and platform APIs before adding a helper or abstraction. Check the package registry before writing solved non-domain infrastructure.

Prefer a maintained package when it meets the repository contract. Check maintenance, adoption, licence compatibility, TypeScript support, runtime compatibility, security advisories, and scope. Use one library per job.

Write custom infrastructure only when existing code, platform APIs, and suitable packages cannot meet the contract. Keep it small, expose a clear boundary, and test its behaviour.

Add dependencies with the configured package manager and commit its lockfile. Do not replace manifest ranges with exact versions to reproduce an install; the lockfile records the exact resolution.

## Architecture

${architecture}

Library code returns values instead of writing process output. It does not read environment variables, configure logging, or depend on an application entry point.

## TypeScript

- Keep strict type checking enabled.
- Use \`unknown\` at untrusted boundaries and narrow it before use.
- Validate external input at runtime. Type assertions do not validate data.
- Model closed variants with discriminated unions and exhaustive checks.
- Keep exported interfaces small and named in the repository's domain language.
- Avoid \`any\`, non-null assertions, ignored type errors, and broad type assertions.

## Configuration

- Keep stable domain and protocol constants in code.
- Put maintainer-controlled values in typed configuration.
- Read deployment values at an application boundary and pass typed values inward.
- Load credentials from the runtime environment or a secret store.
- Keep mutable business and runtime data in its system of record.

Never commit credentials or use a real credential as a default.

## Tests

${testing}

Test observable behaviour. Mock only systems this repository does not own. Use small fakes for local ports. Coverage is a floor; do not lower it to make a change pass.

## Comments

Use comments for constraints and invariants the code cannot express. Keep ticket commentary, change history, narration, and discarded alternatives out of source files.

## Commits

${commits}

Do not bypass Git hooks with \`--no-verify\`.

## Completion checks

Run every applicable repository check before reporting completion:

\`\`\`sh
${commands.join("\n")}
\`\`\`
`;
}

function codingStandards(context: ProviderContext): string {
  const quality = context.profile.quality === "biome"
    ? "Biome"
    : context.profile.quality === "eslint-prettier"
      ? "ESLint and Prettier"
      : "Review";
  const tests = testRunnerName(context.profile.tests);
  const rows = [
    ["Strict type checking, indexed access, and optional property semantics", "TypeScript configuration"],
    ["Formatting, linting, import hygiene, and unsafe language patterns", quality],
    ["External input is narrowed or validated before use", context.profile.runtime_validation === "none" ? "Review" : runtimeValidatorName(context.profile.runtime_validation)],
    ["Public behaviour and package boundaries are tested", tests],
    ["Copied implementations stay below the configured threshold", context.profile.duplication === "jscpd" ? "jscpd" : "Review"],
    ["Credentials stay out of the working tree", context.profile.secret_scan === "gitleaks" ? "Gitleaks" : "Review"],
    ["Commit messages follow Conventional Commits", context.profile.commit_lint === "commitlint" ? "Commitlint" : "Review"],
    ["Configured checks pass before merge", context.profile.ci === "none" ? "Local checks" : ciName(context.profile.ci)],
  ];
  return `# Coding standards

Automate standards when the selected compiler or tooling can express them. Review the remaining design and dependency decisions.

## Enforcement

| Standard | Enforcement |
| --- | --- |
${rows.map(([standard, enforcement]) => `| ${standard} | ${enforcement} |`).join("\n")}

## Dependency decisions

Search existing code, installed dependencies, platform APIs, and the package registry before writing non-domain infrastructure. A new dependency must be maintained, typed, compatibly licensed, free of known unpatched advisories, compatible with the selected runtime, and proportionate to the job.

## Module boundaries

Library modules do not read environment variables, configure logging, write process output, or import application adapters. Applications own configuration loading, composition, transport adapters, and process lifecycle.

## Runtime boundaries

Treat parsed JSON, environment values, request data, messages, and third-party responses as untrusted. Narrow or validate them before they reach domain code.

## Tests

Test public behaviour rather than implementation lines. Unit tests may import source directly. Boundary tests import packages through their public entry points and exercise current build output. Mock external systems, not repository-owned code.

## Repository checks

\`\`\`sh
${completionCommands(context).join("\n")}
\`\`\`
`;
}

function completionCommands(context: ProviderContext): string[] {
  return ["lint", "typecheck", "test", "build", "duplication", "secrets"]
    .filter((script) => context.scripts[script] !== undefined)
    .map((script) => `${context.packageRun} ${script}`);
}

function testRunnerName(value: string): string {
  if (value === "vitest") return "Vitest";
  if (value === "jest") return "Jest";
  if (value === "node-test") return "the Node.js test runner";
  return "Review";
}

function runtimeValidatorName(value: string): string {
  if (value === "zod") return "Zod";
  if (value === "valibot") return "Valibot";
  return "Review";
}

function ciName(value: string): string {
  if (value === "github-actions") return "GitHub Actions";
  if (value === "gitlab-ci") return "GitLab CI";
  return "Local checks";
}
