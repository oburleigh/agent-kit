import type { ProviderContribution } from "../src/types.js";
import { json } from "./helpers.js";

export const qualityProviders: ProviderContribution[] = [
  {
    id: "quality-biome",
    selected: (profile) => profile.quality === "biome",
    devDependencies: { "@biomejs/biome": "^2.5.10" },
    scripts: {
      lint: "biome check .",
      format: "biome check --write .",
    },
    files: () => ({
      "biome.json": json({
        $schema: "https://biomejs.dev/schemas/2.5.10/schema.json",
        vcs: { enabled: true, clientKind: "git", useIgnoreFile: true },
        formatter: { enabled: true, indentStyle: "space" },
        linter: { enabled: true, rules: { preset: "recommended" } },
      }),
    }),
  },
  {
    id: "quality-eslint-prettier",
    selected: (profile) => profile.quality === "eslint-prettier",
    devDependencies: {
      eslint: "^10.9.1",
      "@eslint/js": "^10.0.1",
      "typescript-eslint": "^8.68.0",
      prettier: "^3.9.6",
      "eslint-config-prettier": "^10.1.8",
    },
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
