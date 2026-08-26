import type { ProviderContribution } from "../src/types.js";
import { json } from "./helpers.js";

function requireWorkspace(preset: string): void {
  if (preset !== "workspace") throw new Error("Workspace providers require the workspace preset");
}

export const workspaceProviders: ProviderContribution[] = [
  {
    id: "workspace-turbo",
    selected: (profile) => profile.workspace === "turbo",
    validate: ({ profile }) => requireWorkspace(profile.preset),
    devDependencies: { turbo: "^2.10.12" },
    scripts: { build: "turbo build", test: "turbo test", lint: "turbo lint" },
    packageJson: { workspaces: ["packages/*"] },
    ignore: [".turbo/"],
    files: () => ({
      "turbo.json": json({
        $schema: "https://turbo.build/schema.json",
        tasks: {
          build: { dependsOn: ["^build"], outputs: ["dist/**"] },
          test: { dependsOn: ["^build"], outputs: ["coverage/**"] },
          lint: { dependsOn: ["^lint"] },
        },
      }),
    }),
  },
  {
    id: "workspace-nx",
    selected: (profile) => profile.workspace === "nx",
    validate: ({ profile }) => requireWorkspace(profile.preset),
    devDependencies: { nx: "^23.1.1" },
    scripts: { build: "nx run-many -t build", test: "nx run-many -t test", lint: "nx run-many -t lint" },
    packageJson: { workspaces: ["packages/*"] },
    ignore: [".nx/"],
    files: () => ({
      "nx.json": json({ namedInputs: { default: ["{projectRoot}/**/*"] } }),
    }),
  },
];
