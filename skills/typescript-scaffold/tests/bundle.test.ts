import { readFile } from "node:fs/promises";
import { describe, expect, test } from "vitest";
import { execa } from "execa";

describe("bundled generator", () => {
  test("builds for the declared Node.js baseline", async () => {
    expect(await readFile("scripts/build.mjs", "utf8")).toContain('target: "node24"');
  });

  test("starts without requiring dependencies from the plugin cache", async () => {
    const result = await execa(process.execPath, ["dist/generate.mjs"], { reject: false });

    expect(result.exitCode).toBe(1);
    expect(result.stderr).toContain("--profile and --target are required");
    expect(result.stderr).not.toContain("Dynamic require");
  });

  test("does not contain generated trailing whitespace", async () => {
    expect(await readFile("dist/generate.mjs", "utf8")).not.toMatch(/[ \t]+$/m);
  });
});
