import type { ProviderContribution } from "../src/types.js";

export const publishingProviders: ProviderContribution[] = [
  {
    id: "publishing-npm",
    selected: (profile) => profile.publishing === "npm",
    validate: ({ profile }) => {
      if (profile.preset !== "library") {
        throw new Error("npm publishing requires the library preset");
      }
    },
    packageJson: { private: false, publishConfig: { access: "public" } },
    scripts: (context) => ({ prepublishOnly: `${context.packageRun} build` }),
  },
];
