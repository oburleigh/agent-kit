import { defaultPackageVersions } from "../src/defaults.js";
import type { ScaffoldProfile } from "../src/schema.js";
import type { ProviderContribution } from "../src/types.js";

const sampleTest = `import { describe, expect, test } from "vitest";\nimport { greet } from "../src/index.js";\n\ndescribe("greet", () => {\n  test("greets a named user", () => {\n    expect(greet("Ada")).toBe("Hello, Ada!");\n  });\n});\n`;

function coverageConfig(profile: ScaffoldProfile): string {
  const include = sourceIncludes(profile);
  return `coverage: {
      provider: "v8",
      include: [${quotedList(include)}],
      reporter: ["text", "json-summary", "html"],
      exclude: ["**/*.d.ts", "**/*.test.ts", "**/*.test.tsx", "**/test/**"],
      thresholds: { branches: 80, functions: 80, lines: 80, statements: 80 },
    }`;
}

function sourceIncludes(profile: ScaffoldProfile): string[] {
  if (profile.preset !== "workspace") return ["src/**/*.{ts,tsx}"];
  const members = profile.workspace_members ?? [];
  if (members.length === 0) {
    return ["apps/*/src/**/*.{ts,tsx}", "packages/*/src/**/*.{ts,tsx}"];
  }
  return members.map(({ path }) => `${path}/src/**/*.{ts,tsx}`);
}

function quotedList(values: readonly string[]): string {
  return values.map((value) => `"${value}"`).join(", ");
}

export const testProviders: ProviderContribution[] = [
  {
    id: "tests-vitest",
    selected: (profile) => profile.tests === "vitest" && profile.framework === "none",
    devDependencies: defaultPackageVersions(
      ["vitest", "@vitest/coverage-v8"],
      "tests-vitest",
    ),
    scripts: {
      test: "vitest run",
      "test:watch": "vitest",
      coverage: "vitest run --coverage",
    },
    files: ({ profile }) => ({
      "vitest.config.mts": `import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    ${coverageConfig(profile)},
  },
});
`,
      ...(profile.preset === "library" ? { "test/index.test.ts": sampleTest } : {}),
    }),
  },
  {
    id: "tests-vitest-vite",
    selected: (profile) => profile.tests === "vitest" && profile.framework === "vite-react",
    devDependencies: defaultPackageVersions([
      "vitest",
      "@vitest/coverage-v8",
      "@testing-library/react",
      "@testing-library/jest-dom",
      "jsdom",
    ], "tests-vitest-vite"),
    scripts: {
      test: "vitest run",
      "test:watch": "vitest",
      coverage: "vitest run --coverage",
    },
    files: ({ profile }) => ({
      "vitest.config.mts": `import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test-setup.ts"],
    ${coverageConfig(profile)},
  },
});
`,
      "src/test-setup.ts": "import \"@testing-library/jest-dom/vitest\";\n",
      "src/App.test.tsx": "import { render } from \"@testing-library/react\";\nimport { describe, expect, test } from \"vitest\";\nimport App from \"./App\";\n\ndescribe(\"App\", () => {\n  test(\"renders the application\", () => {\n    const { container } = render(<App />);\n    expect(container.firstChild).not.toBeNull();\n  });\n});\n",
    }),
  },
  {
    id: "tests-node",
    selected: (profile) => profile.tests === "node-test",
    scripts: ({ profile }) => ({
      test: profile.preset === "workspace"
        ? "node --test --experimental-strip-types \"**/*.test.ts\""
        : "node --test --experimental-strip-types test/*.test.ts",
    }),
    files: ({ profile }) => {
      if (profile.preset === "library") {
        return {
          "test/index.test.ts": "import assert from \"node:assert/strict\";\nimport test from \"node:test\";\nimport { greet } from \"../src/index.ts\";\n\ntest(\"greets a named user\", () => {\n  assert.equal(greet(\"Ada\"), \"Hello, Ada!\");\n});\n",
        };
      }
      if (profile.preset === "cli") {
        return {
          "test/cli.test.ts": "import assert from \"node:assert/strict\";\nimport test from \"node:test\";\nimport { greeting } from \"../src/cli.ts\";\n\ntest(\"formats a greeting\", () => {\n  assert.equal(greeting(\"Ada\"), \"Hello, Ada!\");\n});\n",
        };
      }
      return {};
    },
  },
  {
    id: "tests-jest",
    selected: (profile) => profile.tests === "jest",
    devDependencies: defaultPackageVersions(
      ["jest", "@swc/core", "@swc/jest", "@types/jest"],
      "tests-jest",
    ),
    scripts: { test: "jest", "test:watch": "jest --watch", coverage: "jest --coverage" },
    files: ({ profile }) => ({
      "jest.config.mjs": `export default {
  testEnvironment: "node",
  moduleNameMapper: { "^(\\\\.{1,2}/.*)\\\\.js$": "$1" },
  collectCoverageFrom: [${quotedList([
    ...sourceIncludes(profile),
    "!**/*.d.ts",
    "!**/*.test.{ts,tsx}",
  ])}],
  coverageDirectory: "coverage",
  coverageReporters: ["text", "json-summary", "html"],
  coverageThreshold: {
    global: { branches: 80, functions: 80, lines: 80, statements: 80 },
  },
  transform: {
    "^.+\\\\.tsx?$": ["@swc/jest", {
      jsc: {
        parser: { syntax: "typescript", decorators: true },
        transform: { legacyDecorator: true, decoratorMetadata: true },
      },
      module: { type: "commonjs" },
    }],
  },
};
`,
      ...(profile.preset === "library" ? {
        "test/index.test.ts": "import { greet } from \"../src/index.js\";\n\ntest(\"greets a named user\", () => {\n  expect(greet(\"Ada\")).toBe(\"Hello, Ada!\");\n});\n",
      } : {}),
    }),
  },
];
