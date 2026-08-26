import type { ProviderContribution } from "../src/types.js";
import { intersects, validRange } from "semver";
import { json } from "./helpers.js";

function tsconfig(module: "esm" | "commonjs", nestjs: boolean): string {
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
      rootDir: "src",
      outDir: "dist",
      skipLibCheck: true,
      types: ["node"],
      ...(nestjs ? { experimentalDecorators: true, emitDecoratorMetadata: true } : {}),
    },
    include: ["src"],
  });
}

export const buildProviders: ProviderContribution[] = [
  {
    id: "build-tsc",
    selected: (profile) => profile.build === "tsc" && profile.workspace === "none",
    devDependencies: { typescript: "^6.0.3", "@types/node": "^24.13.3" },
    scripts: { build: "tsc -p tsconfig.json", typecheck: "tsc --noEmit" },
    files: (context) => ({
      "tsconfig.json": tsconfig(context.profile.module, context.profile.http === "nestjs"),
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
    scripts: { build: "tsup", typecheck: "tsc --noEmit" },
    files: (context) => ({
      "tsconfig.json": tsconfig(context.profile.module, context.profile.http === "nestjs"),
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
