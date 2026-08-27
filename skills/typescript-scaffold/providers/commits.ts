import { defaultPackageVersions } from "../src/defaults.js";
import type { ProviderContribution } from "../src/types.js";

export const commitProviders: ProviderContribution[] = [
  {
    id: "commits-commitlint",
    selected: (profile) => profile.commit_lint === "commitlint",
    devDependencies: defaultPackageVersions(
      ["@commitlint/cli", "@commitlint/config-conventional"],
      "commits-commitlint",
    ),
    scripts: { commitlint: "commitlint" },
    files: () => ({
      "commitlint.config.mjs": "export default { extends: [\"@commitlint/config-conventional\"] };\n",
    }),
  },
];
