import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    coverage: {
      reporter: ["text", "json-summary"],
    },
    // Subprocess stderr is intermittently lost when test files run in parallel.
    fileParallelism: false,
    include: ["tests/**/*.test.ts"],
  },
});
