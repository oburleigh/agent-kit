import { stringify } from "yaml";
import type { ProviderContribution, ProviderContext } from "../src/types.js";

export const ciProviders: ProviderContribution[] = [
  {
    id: "ci-github-actions",
    selected: (profile) => profile.ci === "github-actions",
    files: (context) => ({
      ".github/workflows/ci.yml": stringify(githubWorkflow(context)),
    }),
  },
  {
    id: "ci-gitlab",
    selected: (profile) => profile.ci === "gitlab-ci",
    files: (context) => ({
      ".gitlab-ci.yml": stringify(gitlabWorkflow(context)),
    }),
  },
];

function githubWorkflow(context: ProviderContext): Record<string, unknown> {
  const testSteps = [
    { uses: "actions/checkout@v4" },
    ...githubPackageManagerSetup(
      context.profile.package_manager,
      context.profile.package_manager_version,
    ),
    { run: installCommand(context.profile.package_manager) },
    ...ciCommands(context).map((run) => ({ run })),
  ];
  return {
    name: "CI",
    on: { pull_request: null, push: { branches: ["main"] } },
    permissions: { contents: "read" },
    jobs: {
      test: { "runs-on": "ubuntu-latest", steps: testSteps },
      ...(context.profile.secret_scan === "gitleaks" ? {
        secrets: {
          "runs-on": "ubuntu-latest",
          steps: [
            { uses: "actions/checkout@v4", with: { "fetch-depth": 0 } },
            { uses: "gitleaks/gitleaks-action@v2" },
          ],
        },
      } : {}),
    },
  };
}

function gitlabWorkflow(context: ProviderContext): Record<string, unknown> {
  const packageManager = context.profile.package_manager;
  const version = context.profile.package_manager_version;
  return {
    image: gitlabImage(packageManager, version),
    stages: ["test"],
    test: {
      stage: "test",
      ...gitlabPackageManagerSetup(packageManager, version),
      script: [installCommand(packageManager), ...ciCommands(context)],
    },
    ...(context.profile.secret_scan === "gitleaks" ? {
      secrets: {
        stage: "test",
        image: "zricethezav/gitleaks:v8.30.1",
        script: ["gitleaks dir . --no-banner"],
      },
    } : {}),
  };
}

function ciCommands(context: ProviderContext): string[] {
  const standard = ["lint", "typecheck", "test", "build", "duplication"]
    .filter((script) => context.scripts[script] !== undefined)
    .map((script) => runScript(context.profile.package_manager, script));
  return [...standard, ...context.profile.ci_commands];
}

function runScript(packageManager: string, script: string): string {
  if (packageManager === "npm") return `npm run ${script}`;
  if (packageManager === "bun") return `bun run ${script}`;
  return `${packageManager} ${script}`;
}

function githubPackageManagerSetup(
  packageManager: string,
  version: string,
): Array<Record<string, unknown>> {
  if (packageManager === "bun") {
    return [{ uses: "oven-sh/setup-bun@v2", with: { "bun-version": version } }];
  }
  if (packageManager === "pnpm") {
    return [
      { uses: "pnpm/action-setup@v4", with: { version } },
      {
        uses: "actions/setup-node@v4",
        with: { "node-version-file": ".node-version", cache: "pnpm" },
      },
    ];
  }
  if (packageManager === "yarn") {
    return [
      { uses: "actions/setup-node@v4", with: { "node-version-file": ".node-version" } },
      { run: "corepack enable" },
      { run: `corepack install --global yarn@${version}` },
    ];
  }
  return [{
    uses: "actions/setup-node@v4",
    with: { "node-version-file": ".node-version", cache: "npm" },
  }, { run: `npm install --global npm@${version}` }];
}

function gitlabImage(packageManager: string, version: string): string {
  return packageManager === "bun" ? `oven/bun:${version}` : "node:24";
}

function gitlabPackageManagerSetup(
  packageManager: string,
  version: string,
): Record<string, string[]> {
  if (packageManager === "npm") {
    return { before_script: [`npm install --global npm@${version}`] };
  }
  if (packageManager !== "pnpm" && packageManager !== "yarn") return {};
  return {
    before_script: [
      "corepack enable",
      `corepack install --global ${packageManager}@${version}`,
    ],
  };
}

function installCommand(packageManager: string): string {
  if (packageManager === "npm") return "npm ci";
  if (packageManager === "yarn") return "yarn install --immutable";
  if (packageManager === "bun") return "bun install --frozen-lockfile";
  return "pnpm install --frozen-lockfile";
}
