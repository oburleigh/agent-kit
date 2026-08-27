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
      "commitlint.config.mjs": `const commitlintConfig = {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "body-leading-blank": [2, "always"],
    "footer-leading-blank": [2, "always"],
    "scope-case": [2, "always", "lower-case"],
  },
};

export default commitlintConfig;
`,
    }),
  },
];
