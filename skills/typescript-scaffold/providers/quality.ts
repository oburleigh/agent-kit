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
      lint: "biome check --error-on-warnings .",
      "lint:fix": "biome check --write --error-on-warnings .",
      format: "biome format --write .",
      "format:check": "biome format .",
    },
    files: (context) => ({
      "biome.json": json({
        $schema: `https://biomejs.dev/schemas/${biomeVersion(context.versionFor(
          "@biomejs/biome",
          defaultPackageVersion("@biomejs/biome", "quality-biome"),
        ))}/schema.json`,
        vcs: { enabled: true, clientKind: "git", useIgnoreFile: true },
        files: {
          includes: [
            "**",
            "!**/.nx",
            "!**/.turbo",
            "!**/build",
            "!**/coverage",
            "!**/dist",
            "!**/node_modules",
            "!**/reports",
            "!**/test-results",
          ],
        },
        formatter: { enabled: true, indentStyle: "space", indentWidth: 2, lineWidth: 100 },
        linter: {
          enabled: true,
          domains: { project: "all", test: "all" },
          rules: {
            preset: "recommended",
            correctness: {
              useImportExtensions: context.profile.framework === "none"
                ? {
                    level: "error",
                    options: { extensionMappings: { ts: "js", tsx: "js" } },
                  }
                : "off",
            },
            suspicious: { noExplicitAny: "error", noTsIgnore: "error" },
            style: {
              ...(context.profile.module === "esm" ? { noCommonJs: "error" } : {}),
              noEnum: "error",
              noNonNullAssertion: "error",
            },
          },
        },
        javascript: { formatter: { quoteStyle: "double", trailingCommas: "all" } },
        ...(context.profile.preset === "workspace"
          ? {
              overrides: [{
                includes: ["**/*.test.ts", "**/*.test.tsx"],
                linter: {
                  rules: { correctness: { noUndeclaredDependencies: "off" } },
                },
              }],
            }
          : {}),
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
      lint: "eslint --max-warnings=0 .",
      "lint:fix": "eslint --fix --max-warnings=0 .",
      format: "prettier --write .",
      "format:check": "prettier --check .",
    },
    files: ({ profile }) => ({
      "eslint.config.mjs": `import eslint from "@eslint/js";
import prettier from "eslint-config-prettier";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["build/**", "coverage/**", "dist/**", "node_modules/**", "reports/**"] },
  eslint.configs.recommended,
  ...tseslint.configs.strict,
  ...tseslint.configs.stylistic,
  {
    rules: {
      ${profile.module === "commonjs"
        ? '"@typescript-eslint/no-require-imports": "off",\n      '
        : ""}"no-restricted-syntax": [
        "error",
        { selector: "TSEnumDeclaration", message: "Use a union or object literal instead of an enum." },
      ],
    },
  },
  prettier,
);
`,
      ".prettierrc.json": json({
        printWidth: 100,
        semi: true,
        singleQuote: false,
        tabWidth: 2,
        trailingComma: "all",
      }),
      ".prettierignore": "build\ncoverage\ndist\nnode_modules\nreports\n",
    }),
  },
];

function biomeVersion(range: string): string {
  const version = minVersion(range);
  if (version === null) throw new Error(`Invalid Biome version range: ${range}`);
  return version.version;
}
