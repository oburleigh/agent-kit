import { access, copyFile, mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { Worker } from "node:worker_threads";
import { stringify } from "yaml";
import { describe, expect, onTestFinished, test } from "vitest";
import { loadBundledPreset } from "../src/profiles.js";

const bundleLoader = `
const { parentPort, workerData } = require("node:worker_threads");
import(workerData)
  .then(({ main }) => main([]))
  .then(() => parentPort.postMessage(""))
  .catch((error) => parentPort.postMessage(error instanceof Error ? error.message : String(error)));
`;

const bundlePlanLoader = `
const { parentPort, workerData } = require("node:worker_threads");
import(workerData.url)
  .then(({ main }) => main(workerData.args))
  .then((result) => parentPort.postMessage(result))
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

  test("plans without writing a repository through the published bundle", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-bundle-plan-"));
    onTestFinished(() => rm(root, { recursive: true, force: true }));
    const dist = join(root, "dist");
    const config = join(root, "config");
    const profilePath = join(root, "profile.yaml");
    const target = join(root, "planned-library");
    await mkdir(dist);
    await mkdir(config);
    const bundledGenerator = join(dist, "generate.mjs");
    await copyFile("dist/generate.mjs", bundledGenerator);
    await copyFile("config/defaults.yaml", join(config, "defaults.yaml"));
    await writeFile(profilePath, stringify(await loadBundledPreset("library")));

    const worker = new Worker(bundlePlanLoader, {
      eval: true,
      workerData: {
        url: pathToFileURL(bundledGenerator).href,
        args: ["--profile", profilePath, "--target", target, "--plan"],
      },
    });
    onTestFinished(async () => {
      await worker.terminate();
    });
    const result = await new Promise<unknown>((resolve, reject) => {
      worker.once("message", resolve);
      worker.once("error", reject);
    });

    expect(typeof result).toBe("string");
    expect(JSON.parse(String(result))).toMatchObject({ target });
    await expect(access(target)).rejects.toMatchObject({ code: "ENOENT" });
  });

  test("does not contain generated trailing whitespace", async () => {
    expect(await readFile("dist/generate.mjs", "utf8")).not.toMatch(/[ \t]+$/m);
  });
});
