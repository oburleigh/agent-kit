import type { ProviderContribution } from "../src/types.js";
import { intersects, validRange } from "semver";
import { json } from "./helpers.js";

function tsconfig(
  module: "esm" | "commonjs",
  nestjs: boolean,
  tests: "vitest" | "node-test" | "jest" | "none",
): string {
  return json({
    compilerOptions: {
      target: "ES2023",
      module: module === "esm" ? "NodeNext" : "CommonJS",
      moduleResolution: module === "esm" ? "NodeNext" : "Node",
      strict: true,
      noUncheckedIndexedAccess: true,
      exactOptionalPropertyTypes: true,
      declaration: true,
      sourceMap: true,
      skipLibCheck: true,
      types: tests === "jest" ? ["node", "jest"] : ["node"],
      ...(nestjs ? { experimentalDecorators: true, emitDecoratorMetadata: true } : {}),
    },
    include: ["src", "test", "*.config.*"],
  });
}

function buildTsconfig(): string {
  return json({
    extends: "./tsconfig.json",
    compilerOptions: { rootDir: "src", outDir: "dist" },
    include: ["src"],
    exclude: ["test", "**/*.test.ts", "**/*.test.tsx"],
  });
}

export const buildProviders: ProviderContribution[] = [
  {
    id: "build-tsc",
    selected: (profile) => profile.build === "tsc" && profile.workspace === "none",
    devDependencies: { typescript: "^6.0.3", "@types/node": "^24.13.3" },
    scripts: ({ profile }) => ({
      build: "tsc -p tsconfig.build.json",
      typecheck: profile.tests === "node-test"
        ? "tsc --noEmit --allowImportingTsExtensions"
        : "tsc --noEmit",
    }),
    files: (context) => ({
      "tsconfig.json": tsconfig(
        context.profile.module,
        context.profile.http === "nestjs",
        context.profile.tests,
      ),
      "tsconfig.build.json": buildTsconfig(),
    }),
  },
  {
    id: "build-tsup",
    selected: (profile) => profile.build === "tsup" && profile.workspace === "none",
    validate: ({ profile }) => {
      const typescriptRange = profile.package_versions.typescript ?? "^5.9.3";
      if (!validRange(typescriptRange) || intersects(typescriptRange, ">=6.0.0")) {
        throw new Error(
          "tsup declaration generation requires TypeScript 5.9. Use the tsc build provider for TypeScript 6 or set package_versions.typescript to ^5.9.3.",
        );
      }
    },
    devDependencies: {
      typescript: "^5.9.3",
      "@types/node": "^24.13.3",
      tsup: "^8.5.1",
    },
    scripts: ({ profile }) => ({
      build: "tsup",
      typecheck: profile.tests === "node-test"
        ? "tsc --noEmit --allowImportingTsExtensions"
        : "tsc --noEmit",
    }),
    files: (context) => ({
      "tsconfig.json": tsconfig(
        context.profile.module,
        context.profile.http === "nestjs",
        context.profile.tests,
      ),
      "tsconfig.build.json": buildTsconfig(),
      "tsup.config.ts": `import { defineConfig } from "tsup";\n\nexport default defineConfig({\n  entry: ["${entryPoint(context.profile.preset)}"],\n  format: ["${context.profile.module === "esm" ? "esm" : "cjs"}"],\n  dts: true,\n  sourcemap: true,\n  clean: true,\n});\n`,
    }),
  },
  {
    id: "build-framework",
    selected: (profile) => profile.build === "framework-owned",
    validate: ({ profile }) => {
      if (profile.framework === "none") {
        throw new Error("framework-owned build requires a framework adapter");
      }
    },
  },
];

function entryPoint(preset: "library" | "service" | "cli" | "workspace"): string {
  if (preset === "cli") return "src/cli.ts";
  if (preset === "service") return "src/server.ts";
  return "src/index.ts";
}
