import type { ProviderContribution } from "../src/types.js";
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
    devDependencies: { jscpd: "^5.0.16" },
    scripts: { duplication: "jscpd src" },
    files: () => ({
      ".jscpd.json": json({ threshold: 0, reporters: ["console"], ignore: ["**/dist/**"] }),
    }),
  },
];
