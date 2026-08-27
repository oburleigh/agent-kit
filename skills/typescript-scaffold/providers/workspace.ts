import { posix } from "node:path";
import { defaultPackageVersions, scaffoldDefaults } from "../src/defaults.js";
import type { ScaffoldProfile } from "../src/schema.js";
import type { ProviderContribution, ProviderContext } from "../src/types.js";
import { json } from "./helpers.js";

const workspaceDevDependencies = defaultPackageVersions(
  ["typescript", "@types/node"],
  "workspace",
);

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
    scripts: { build: "turbo build", typecheck: "turbo typecheck" },
    packageJson: workspacePackageJson,
    ignore: [".turbo/"],
    files: (context) => ({
      "turbo.json": json({
        $schema: "https://turbo.build/schema.json",
        tasks: {
          build: { dependsOn: ["^build"], outputs: ["dist/**"] },
          typecheck: { dependsOn: ["^typecheck"] },
        },
      }),
      ...workspaceFiles(context),
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
    scripts: { build: "nx run-many -t build", typecheck: "nx run-many -t typecheck" },
    packageJson: workspacePackageJson,
    ignore: [".nx/"],
    files: (context) => ({
      "nx.json": json({ namedInputs: { default: ["{projectRoot}/**/*"] } }),
      ...workspaceFiles(context),
    }),
  },
];

function workspacePackageJson(context: ProviderContext): Record<string, unknown> {
  return { workspaces: workspacePaths(context.profile) };
}

function workspacePaths(profile: ScaffoldProfile): string[] {
  const members = profile.workspace_members ?? [];
  return members.length > 0 ? members.map(({ path }) => path) : ["apps/*", "packages/*"];
}

function workspaceFiles(context: ProviderContext): Record<string, string> {
  const paths = workspacePaths(context.profile);
  return {
    "tsconfig.base.json": workspaceTsconfig(context.profile),
    ...(context.profile.package_manager === "pnpm"
      ? { "pnpm-workspace.yaml": `packages:\n${paths.map((path) => `  - ${path}`).join("\n")}\n` }
      : {}),
    ...memberFiles(context),
  };
}

function memberFiles(context: ProviderContext): Record<string, string> {
  return Object.fromEntries(
    (context.profile.workspace_members ?? []).flatMap((member) => {
      const packageName = member.package_name.replaceAll("{project}", context.project.name);
      const root = posix.relative(member.path, ".");
      const sourceName = member.kind === "application" ? "applicationName" : "packageName";
      const files: Array<[string, string]> = [
        [`${member.path}/package.json`, json({
          name: packageName,
          version: scaffoldDefaults.generated_package_version,
          private: true,
          type: context.profile.module === "esm" ? "module" : "commonjs",
          main: "./dist/index.js",
          types: "./dist/index.d.ts",
          scripts: {
            build: "tsc -p tsconfig.build.json",
            typecheck: context.profile.tests === "node-test"
              ? "tsc --noEmit --allowImportingTsExtensions"
              : "tsc --noEmit",
          },
        })],
        [`${member.path}/tsconfig.json`, json({
          extends: `${root}/tsconfig.base.json`,
          compilerOptions: { noEmit: true },
          include: ["src", "test"],
        })],
        [`${member.path}/tsconfig.build.json`, json({
          extends: "./tsconfig.json",
          compilerOptions: {
            noEmit: false,
            rootDir: "src",
            outDir: "dist",
            declaration: true,
            sourceMap: true,
          },
          include: ["src"],
          exclude: ["test", "**/*.test.ts"],
        })],
        [`${member.path}/src/index.ts`, `export const ${sourceName} = "${packageName}";\n`],
      ];
      const test = memberTest(context.profile.tests, sourceName, packageName);
      if (test !== undefined) files.push([`${member.path}/test/index.test.ts`, test]);
      return files;
    }),
  );
}

function workspaceTsconfig(profile: ScaffoldProfile): string {
  return json({
    compilerOptions: {
      target: scaffoldDefaults.runtime.typescript_target,
      module: "NodeNext",
      moduleResolution: "NodeNext",
      strict: true,
      noUncheckedIndexedAccess: true,
      exactOptionalPropertyTypes: true,
      skipLibCheck: true,
      types: profile.tests === "jest" ? ["node", "jest"] : ["node"],
    },
  });
}

function memberTest(
  runner: ScaffoldProfile["tests"],
  sourceName: string,
  packageName: string,
): string | undefined {
  if (runner === "none") return undefined;
  if (runner === "node-test") {
    return `import assert from "node:assert/strict";\nimport test from "node:test";\nimport { ${sourceName} } from "../src/index.ts";\n\ntest("exports its package name", () => {\n  assert.equal(${sourceName}, "${packageName}");\n});\n`;
  }
  const imports = runner === "vitest"
    ? "import { expect, test } from \"vitest\";\n"
    : "";
  return `${imports}import { ${sourceName} } from "../src/index.js";\n\ntest("exports its package name", () => {\n  expect(${sourceName}).toBe("${packageName}");\n});\n`;
}
