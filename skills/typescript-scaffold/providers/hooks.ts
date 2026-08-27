import type { ProviderContext, ProviderContribution } from "../src/types.js";
import { defaultPackageVersions } from "../src/defaults.js";
import { stringify } from "yaml";
import { json } from "./helpers.js";

export const hookProviders: ProviderContribution[] = [
  {
    id: "hooks-lefthook",
    selected: (profile) => profile.hooks === "lefthook",
    validate: ({ profile }) => {
      if (profile.quality === "none" && profile.tests === "none" && profile.workspace === "none") {
        throw new Error("Lefthook requires a lint or test provider");
      }
    },
    devDependencies: defaultPackageVersions(["lefthook"], "hooks-lefthook"),
    scripts: { prepare: "lefthook install" },
    files: (context) => {
      const preCommitCommands = lefthookPreCommitCommands(context);
      const prePushCommands = Object.fromEntries(
        ["typecheck", "test"]
          .filter((script) => context.scripts[script] !== undefined)
          .map((script) => [script, { run: `${context.packageRun} ${script}` }]),
      );
      const commitMessage = context.profile.commit_lint === "commitlint"
        ? {
            "commit-msg": {
              commands: { commitlint: { run: commitlintCommand(context.profile.package_manager, "{1}") } },
            },
          }
        : {};
      return {
        "lefthook.yml": stringify({
          ...(Object.keys(preCommitCommands).length > 0
            ? { "pre-commit": { commands: preCommitCommands } }
            : {}),
          ...commitMessage,
          ...(Object.keys(prePushCommands).length > 0
            ? { "pre-push": { parallel: true, commands: prePushCommands } }
            : {}),
        }),
      };
    },
  },
  {
    id: "hooks-husky-lint-staged",
    selected: (profile) => profile.hooks === "husky-lint-staged",
    devDependencies: defaultPackageVersions(
      ["husky", "lint-staged"],
      "hooks-husky-lint-staged",
    ),
    scripts: { prepare: "husky" },
    files: (context) => {
      const prePush = ["typecheck", "test"]
        .filter((script) => context.scripts[script] !== undefined)
        .map((script) => `${context.packageRun} ${script}`)
        .join("\n");
      return {
        ".husky/pre-commit": `${packageExecCommand(context.profile.package_manager, "lint-staged")}\n`,
        ...(context.profile.commit_lint === "commitlint"
          ? { ".husky/commit-msg": `${commitlintCommand(context.profile.package_manager, '"$1"')}\n` }
          : {}),
        ...(prePush ? { ".husky/pre-push": `${prePush}\n` } : {}),
        ".lintstagedrc.json": json({
          "*.{js,mjs,cjs,ts,tsx}": [
            "eslint --fix --max-warnings=0",
            "prettier --write",
          ],
          "*.{json,jsonc,css,md,yml,yaml}": "prettier --write",
        }),
      };
    },
  },
];

function commitlintCommand(packageManager: string, messageFile: string): string {
  return `${packageExecCommand(packageManager, "commitlint")} --edit ${messageFile}`;
}

function packageExecCommand(packageManager: string, binary: string): string {
  if (packageManager === "bun") return `bunx ${binary}`;
  if (packageManager === "npm") return `npm exec -- ${binary}`;
  return `${packageManager} exec ${binary}`;
}

function lefthookPreCommitCommands(context: ProviderContext): Record<string, object> {
  if (context.profile.quality === "biome") {
    return {
      quality: {
        glob: "*.{ts,tsx,js,mjs,cjs,json,jsonc,css,md,yml,yaml}",
        run: `${packageExecCommand(context.profile.package_manager, "biome")} check --write --error-on-warnings --no-errors-on-unmatched {staged_files}`,
        stage_fixed: true,
      },
    };
  }
  if (context.profile.quality === "eslint-prettier") {
    return {
      lint: {
        glob: "*.{js,mjs,cjs,ts,tsx}",
        run: `${packageExecCommand(context.profile.package_manager, "eslint")} --fix --max-warnings=0 {staged_files}`,
        stage_fixed: true,
      },
      format: {
        glob: "*.{js,mjs,cjs,ts,tsx,json,jsonc,css,md,yml,yaml}",
        run: `${packageExecCommand(context.profile.package_manager, "prettier")} --write {staged_files}`,
        stage_fixed: true,
      },
    };
  }
  if (context.scripts.lint === undefined) return {};
  return { lint: { run: `${context.packageRun} lint` } };
}
