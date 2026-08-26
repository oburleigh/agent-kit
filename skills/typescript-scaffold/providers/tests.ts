import type { ProviderContribution } from "../src/types.js";

const sampleTest = `import { describe, expect, test } from "vitest";\nimport { greet } from "../src/index.js";\n\ndescribe("greet", () => {\n  test("greets a named user", () => {\n    expect(greet("Ada")).toBe("Hello, Ada!");\n  });\n});\n`;

export const testProviders: ProviderContribution[] = [
  {
    id: "tests-vitest",
    selected: (profile) => profile.tests === "vitest" && profile.framework === "none",
    devDependencies: { vitest: "^4.1.11", "@vitest/coverage-v8": "^4.1.11" },
    scripts: {
      test: "vitest run",
      "test:watch": "vitest",
      coverage: "vitest run --coverage",
    },
    files: ({ profile }) => ({
      "vitest.config.ts": "import { defineConfig } from \"vitest/config\";\n\nexport default defineConfig({\n  test: { coverage: { provider: \"v8\", reporter: [\"text\", \"json-summary\"] } },\n});\n",
      ...(profile.preset === "library" ? { "test/index.test.ts": sampleTest } : {}),
    }),
  },
  {
    id: "tests-vitest-vite",
    selected: (profile) => profile.tests === "vitest" && profile.framework === "vite-react",
    devDependencies: {
      vitest: "^4.1.11",
      "@vitest/coverage-v8": "^4.1.11",
      "@testing-library/react": "^16.3.2",
      "@testing-library/jest-dom": "^7.0.1",
      jsdom: "^30.0.1",
    },
    scripts: {
      test: "vitest run",
      "test:watch": "vitest",
      coverage: "vitest run --coverage",
    },
    files: () => ({
      "vitest.config.ts": "import react from \"@vitejs/plugin-react\";\nimport { defineConfig } from \"vitest/config\";\n\nexport default defineConfig({\n  plugins: [react()],\n  test: {\n    environment: \"jsdom\",\n    setupFiles: [\"./src/test-setup.ts\"],\n    coverage: { provider: \"v8\", reporter: [\"text\", \"json-summary\"] },\n  },\n});\n",
      "src/test-setup.ts": "import \"@testing-library/jest-dom/vitest\";\n",
      "src/App.test.tsx": "import { render } from \"@testing-library/react\";\nimport { describe, expect, test } from \"vitest\";\nimport App from \"./App\";\n\ndescribe(\"App\", () => {\n  test(\"renders the application\", () => {\n    const { container } = render(<App />);\n    expect(container.firstChild).not.toBeNull();\n  });\n});\n",
    }),
  },
  {
    id: "tests-node",
    selected: (profile) => profile.tests === "node-test",
    scripts: { test: "node --test --experimental-strip-types test/*.test.ts" },
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
    devDependencies: {
      jest: "^30.2.0",
      "@swc/core": "^1.16.1",
      "@swc/jest": "^0.2.39",
      "@types/jest": "^30.0.0",
    },
    scripts: { test: "jest", "test:watch": "jest --watch" },
    files: ({ profile }) => ({
      "jest.config.mjs": "export default {\n  testEnvironment: \"node\",\n  transform: {\n    \"^.+\\\\.tsx?$\": [\"@swc/jest\", {\n      jsc: {\n        parser: { syntax: \"typescript\", decorators: true },\n        transform: { legacyDecorator: true, decoratorMetadata: true },\n      },\n      module: { type: \"commonjs\" },\n    }],\n  },\n};\n",
      ...(profile.preset === "library" ? {
        "test/index.test.ts": "import { greet } from \"../src/index\";\n\ntest(\"greets a named user\", () => {\n  expect(greet(\"Ada\")).toBe(\"Hello, Ada!\");\n});\n",
      } : {}),
    }),
  },
];
