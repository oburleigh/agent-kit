import type { ProviderContribution } from "../src/types.js";

export const moduleProviders: ProviderContribution[] = [
  {
    id: "module-esm",
    selected: (profile) => profile.module === "esm",
    packageJson: { type: "module" },
  },
  {
    id: "module-commonjs",
    selected: (profile) => profile.module === "commonjs",
    packageJson: { type: "commonjs" },
    validate: ({ profile }) => {
      if (profile.framework === "vite-react") {
        throw new Error("The Vite React framework requires ESM");
      }
    },
  },
];
