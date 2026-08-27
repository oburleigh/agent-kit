import type { ProviderContribution } from "../src/types.js";
import { defaultPackageVersions } from "../src/defaults.js";
import { json } from "./helpers.js";

export const checkProviders: ProviderContribution[] = [
  {
    id: "secret-gitleaks",
    selected: (profile) => profile.secret_scan === "gitleaks",
    scripts: { secrets: "gitleaks dir . --no-banner" },
    files: () => ({
      ".gitleaks.toml": "title = \"gitleaks configuration\"\n\n[extend]\nuseDefault = true\n",
    }),
  },
  {
    id: "duplication-jscpd",
    selected: (profile) => profile.duplication === "jscpd",
    devDependencies: defaultPackageVersions(["jscpd"], "duplication-jscpd"),
    scripts: ({ profile }) => ({
      duplication: profile.preset === "workspace"
        ? `jscpd ${(profile.workspace_members ?? [])
          .map(({ path }) => `${path}/src`)
          .join(" ") || "apps packages"}`
        : "jscpd src",
    }),
    files: ({ profile }) => ({
      ".jscpd.json": json({
        threshold: 0,
        reporters: ["console"],
        ignore: ["**/dist/**"],
        ...(profile.preset === "workspace" ? { minLines: 1, minTokens: 5 } : {}),
      }),
    }),
  },
];
