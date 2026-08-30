import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, test } from "vitest";
import { loadBundledPreset } from "../src/profiles.js";
import { createPlanSummary } from "../src/summary.js";

describe("plan summaries", () => {
  test("includes quality gates owned by the Vite generator", async () => {
    const profile = await loadBundledPreset("library");
    Object.assign(profile, {
      package_manager: "npm",
      package_manager_version: "11.17.0",
      build: "framework-owned",
      quality: "none",
      tests: "none",
      hooks: "none",
      commit_lint: "none",
      publishing: "none",
      secret_scan: "none",
      duplication: "none",
      framework: "vite-react",
    });

    const summary = createPlanSummary(profile, join(tmpdir(), "web-app"));

    expect(summary.quality_gates).toEqual(["npm run lint", "npm run build"]);
  });

  test("resolves workspace package-name templates", async () => {
    const profile = await loadBundledPreset("workspace");

    const summary = createPlanSummary(profile, join(tmpdir(), "platform"));

    expect(summary.workspace_members).toEqual([
      { path: "apps/app", package_name: "@platform/app", kind: "application" },
      { path: "packages/core", package_name: "@platform/core", kind: "library" },
    ]);
  });
});
