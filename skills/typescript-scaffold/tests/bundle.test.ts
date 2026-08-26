import { copyFile, mkdir, mkdtemp, readFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, test } from "vitest";
import { execa } from "execa";

describe("bundled generator", () => {
  test("builds for the declared Node.js baseline", async () => {
    expect(await readFile("scripts/build.mjs", "utf8")).toContain('target: "node24"');
  });

  test("starts without requiring dependencies from the plugin cache", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-bundle-"));
    const dist = join(root, "dist");
    const config = join(root, "config");
    await mkdir(dist);
    await mkdir(config);
    await copyFile("dist/generate.mjs", join(dist, "generate.mjs"));
    await copyFile("config/defaults.yaml", join(config, "defaults.yaml"));

    const result = await execa(process.execPath, [join(dist, "generate.mjs")], {
      cwd: root,
      reject: false,
    });

    expect(result.exitCode).toBe(1);
    expect(result.stderr).toContain("--profile and --target are required");
    expect(result.stderr).not.toContain("Dynamic require");
  });

  test("does not contain generated trailing whitespace", async () => {
    expect(await readFile("dist/generate.mjs", "utf8")).not.toMatch(/[ \t]+$/m);
  });
});
