import type { ProviderContribution } from "../src/types.js";
import { defaultPackageVersions } from "../src/defaults.js";

export const validationProviders: ProviderContribution[] = [
  {
    id: "validation-zod",
    selected: (profile) => profile.runtime_validation === "zod",
    dependencies: defaultPackageVersions(["zod"], "validation-zod"),
  },
  {
    id: "validation-valibot",
    selected: (profile) => profile.runtime_validation === "valibot",
    dependencies: defaultPackageVersions(["valibot"], "validation-valibot"),
  },
];
