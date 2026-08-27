import { copyFile, mkdir, mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { Worker } from "node:worker_threads";
import { describe, expect, onTestFinished, test } from "vitest";

const bundleLoader = `
const { parentPort, workerData } = require("node:worker_threads");
import(workerData)
  .then(({ main }) => main([]))
  .then(() => parentPort.postMessage(""))
  .catch((error) => parentPort.postMessage(error instanceof Error ? error.message : String(error)));
`;

describe("bundled generator", () => {
  test("builds for the declared Node.js baseline", async () => {
    expect(await readFile("scripts/build.mjs", "utf8")).toContain('target: "node24"');
  });

  test("starts without requiring dependencies from the plugin cache", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-bundle-"));
    onTestFinished(() => rm(root, { recursive: true, force: true }));
    const dist = join(root, "dist");
    const config = join(root, "config");
    await mkdir(dist);
    await mkdir(config);
    const bundledGenerator = join(dist, "generate.mjs");
    await copyFile("dist/generate.mjs", bundledGenerator);
    await copyFile("config/defaults.yaml", join(config, "defaults.yaml"));

    const worker = new Worker(bundleLoader, {
      eval: true,
      workerData: pathToFileURL(bundledGenerator).href,
    });
    onTestFinished(async () => {
      await worker.terminate();
    });
    const errorMessage = await new Promise<string>((resolve, reject) => {
      worker.once("message", resolve);
      worker.once("error", reject);
    });

    expect(errorMessage).toBe("--profile and --target are required");
  });

  test("does not contain generated trailing whitespace", async () => {
    expect(await readFile("dist/generate.mjs", "utf8")).not.toMatch(/[ \t]+$/m);
  });
});
