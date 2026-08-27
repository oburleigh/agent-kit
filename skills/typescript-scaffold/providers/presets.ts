import type { ProviderContribution } from "../src/types.js";
import { defaultPackageVersions } from "../src/defaults.js";

export const presetProviders: ProviderContribution[] = [
  {
    id: "preset-library",
    selected: (profile) => profile.preset === "library" && profile.framework === "none",
    packageJson: {
      exports: "./dist/index.js",
      types: "./dist/index.d.ts",
      files: ["dist", "README.md"],
    },
    files: () => ({
      "src/index.ts": "export function greet(name: string): string {\n  return `Hello, ${name}!`;\n}\n",
    }),
  },
  {
    id: "preset-service",
    selected: (profile) => profile.preset === "service" && profile.framework === "none",
    packageJson: { private: true },
    scripts: { dev: "tsx watch src/server.ts", start: "node dist/server.js" },
    devDependencies: defaultPackageVersions(["tsx"], "preset-service"),
  },
  {
    id: "preset-cli",
    selected: (profile) => profile.preset === "cli",
    packageJson: { bin: { cli: "./dist/cli.js" } },
    scripts: { dev: "tsx src/cli.ts", start: "node dist/cli.js" },
    devDependencies: defaultPackageVersions(["tsx"], "preset-cli"),
    files: () => ({
      "src/cli.ts": "#!/usr/bin/env node\n\nimport { resolve } from \"node:path\";\nimport { pathToFileURL } from \"node:url\";\n\nexport function greeting(name: string): string {\n  return `Hello, ${name}!`;\n}\n\nconst executablePath = process.argv[1] ? pathToFileURL(resolve(process.argv[1])).href : \"\";\nif (import.meta.url === executablePath) {\n  console.log(greeting(process.argv[2] ?? \"world\"));\n}\n",
    }),
  },
  {
    id: "preset-workspace",
    selected: (profile) => profile.preset === "workspace",
    packageJson: { private: true },
    files: ({ profile }) => (profile.workspace_members ?? []).length === 0
      ? { "packages/.gitkeep": "" }
      : {},
  },
];
