import { defaultPackageVersions, scaffoldDefaults } from "../src/defaults.js";
import type { ProviderContribution } from "../src/types.js";
import { json } from "./helpers.js";

const workspaceDevDependencies = defaultPackageVersions(
  ["typescript", "@types/node"],
  "workspace",
);

const workspaceTsconfig = json({
  compilerOptions: {
    target: scaffoldDefaults.runtime.typescript_target,
    module: "NodeNext",
    moduleResolution: "NodeNext",
    strict: true,
    noUncheckedIndexedAccess: true,
    exactOptionalPropertyTypes: true,
    skipLibCheck: true,
    types: ["node"],
  },
});

function requireWorkspace(preset: string): void {
  if (preset !== "workspace") throw new Error("Workspace providers require the workspace preset");
}

export const workspaceProviders: ProviderContribution[] = [
  {
    id: "workspace-turbo",
    selected: (profile) => profile.workspace === "turbo",
    validate: ({ profile }) => requireWorkspace(profile.preset),
    devDependencies: {
      ...defaultPackageVersions(["turbo"], "workspace-turbo"),
      ...workspaceDevDependencies,
    },
    scripts: {
      build: "turbo build",
      typecheck: "turbo typecheck",
      test: "turbo test",
      lint: "turbo lint",
    },
    packageJson: { workspaces: ["packages/*"] },
    ignore: [".turbo/"],
    files: (context) => ({
      "turbo.json": json({
        $schema: "https://turbo.build/schema.json",
        tasks: {
          build: { dependsOn: ["^build"], outputs: ["dist/**"] },
          typecheck: { dependsOn: ["^typecheck"] },
          test: { dependsOn: ["^build"], outputs: ["coverage/**"] },
          lint: { dependsOn: ["^lint"] },
        },
      }),
      "tsconfig.base.json": workspaceTsconfig,
      ...(context.profile.package_manager === "pnpm"
        ? { "pnpm-workspace.yaml": "packages:\n  - packages/*\n" }
        : {}),
    }),
  },
  {
    id: "workspace-nx",
    selected: (profile) => profile.workspace === "nx",
    validate: ({ profile }) => requireWorkspace(profile.preset),
    devDependencies: {
      ...defaultPackageVersions(["nx"], "workspace-nx"),
      ...workspaceDevDependencies,
    },
    scripts: {
      build: "nx run-many -t build",
      typecheck: "nx run-many -t typecheck",
      test: "nx run-many -t test",
      lint: "nx run-many -t lint",
    },
    packageJson: { workspaces: ["packages/*"] },
    ignore: [".nx/"],
    files: (context) => ({
      "nx.json": json({ namedInputs: { default: ["{projectRoot}/**/*"] } }),
      "tsconfig.base.json": workspaceTsconfig,
      ...(context.profile.package_manager === "pnpm"
        ? { "pnpm-workspace.yaml": "packages:\n  - packages/*\n" }
        : {}),
    }),
  },
];
