import type { ProviderContribution } from "../src/types.js";
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
      const commands = Object.fromEntries(
        ["lint", "test"]
          .filter((script) => context.scripts[script] !== undefined)
          .map((script) => [script, { run: `${context.packageRun} ${script}` }]),
      );
      return {
        "lefthook.yml": stringify({
          "pre-commit": { parallel: true, commands },
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
    files: (context) => ({
      ".husky/pre-commit": `${context.packageCommand} exec lint-staged\n`,
      ".lintstagedrc.json": json({ "*.{js,mjs,cjs,ts,tsx,json,md,yml,yaml}": "prettier --write" }),
    }),
  },
];
