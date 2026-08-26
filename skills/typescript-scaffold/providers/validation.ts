import type { ProviderContribution } from "../src/types.js";

export const validationProviders: ProviderContribution[] = [
  {
    id: "validation-zod",
    selected: (profile) => profile.runtime_validation === "zod",
    dependencies: { zod: "^4.4.3" },
  },
  {
    id: "validation-valibot",
    selected: (profile) => profile.runtime_validation === "valibot",
    dependencies: { valibot: "^1.2.0" },
  },
];
