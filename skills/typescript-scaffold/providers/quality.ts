import { minVersion } from "semver";
import { defaultPackageVersion, defaultPackageVersions } from "../src/defaults.js";
import type { ProviderContribution } from "../src/types.js";
import { json } from "./helpers.js";

export const qualityProviders: ProviderContribution[] = [
  {
    id: "quality-biome",
    selected: (profile) => profile.quality === "biome",
    devDependencies: defaultPackageVersions(["@biomejs/biome"], "quality-biome"),
    scripts: {
      lint: "biome check .",
      format: "biome check --write .",
    },
    files: (context) => ({
      "biome.json": json({
        $schema: `https://biomejs.dev/schemas/${biomeVersion(context.versionFor(
          "@biomejs/biome",
          defaultPackageVersion("@biomejs/biome", "quality-biome"),
        ))}/schema.json`,
        vcs: { enabled: true, clientKind: "git", useIgnoreFile: true },
        formatter: { enabled: true, indentStyle: "space" },
        linter: { enabled: true, rules: { preset: "recommended" } },
      }),
    }),
  },
  {
    id: "quality-eslint-prettier",
    selected: (profile) => profile.quality === "eslint-prettier",
    devDependencies: defaultPackageVersions([
      "eslint",
      "@eslint/js",
      "typescript-eslint",
      "prettier",
      "eslint-config-prettier",
    ], "quality-eslint-prettier"),
    scripts: {
      lint: "eslint .",
      format: "prettier --write .",
      "format:check": "prettier --check .",
    },
    files: () => ({
      "eslint.config.js": "import eslint from \"@eslint/js\";\nimport prettier from \"eslint-config-prettier\";\nimport tseslint from \"typescript-eslint\";\n\nexport default tseslint.config(\n  eslint.configs.recommended,\n  ...tseslint.configs.recommended,\n  prettier,\n  { ignores: [\"dist/**\", \"coverage/**\"] },\n);\n",
      ".prettierrc.json": json({ semi: true, singleQuote: false }),
    }),
  },
];

function biomeVersion(range: string): string {
  const version = minVersion(range);
  if (version === null) throw new Error(`Invalid Biome version range: ${range}`);
  return version.version;
}
