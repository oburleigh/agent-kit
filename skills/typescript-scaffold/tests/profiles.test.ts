import { mkdtemp, readFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { stringify } from "yaml";
import { describe, expect, test } from "vitest";
import { loadProfileText } from "../src/profile.js";

async function loadProfilesModule() {
  return import("../src/profiles.js").catch(() => ({
    createProfileFromPreset: () => {
      throw new Error("profiles module missing");
    },
    loadBundledPreset: () => {
      throw new Error("profiles module missing");
    },
    resolveProfileDirectory: () => {
      throw new Error("profiles module missing");
    },
  }));
}

describe("bundled presets", () => {
  test.each(["library", "service", "cli", "workspace"] as const)(
    "loads a fully materialized %s preset",
    async (preset) => {
      const { loadBundledPreset } = await loadProfilesModule();
      const profile = await loadBundledPreset(preset);

      expect(profile.preset).toBe(preset);
      expect(profile.schema_version).toBe(1);
      expect(profile.package_manager_version).not.toBe("");
      expect(profile.package_versions).toBeTypeOf("object");
    },
  );

  test("rejects a package manager major without an exact version", async () => {
    const { loadBundledPreset } = await loadProfilesModule();
    const profile = await loadBundledPreset("service");

    expect(() => loadProfileText(stringify({ ...profile, package_manager_version: "11" })))
      .toThrow(/exact semantic version/);
  });
});

describe("persistent profiles", () => {
  test("uses the explicit agent-kit config root", async () => {
    const { resolveProfileDirectory } = await loadProfilesModule();

    expect(resolveProfileDirectory({ AGENT_KIT_CONFIG_DIR: "/tmp/example-config" }))
      .toBe("/tmp/example-config/scaffolds/typescript");
  });

  test("creates a named profile once and preserves it on a second request", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-profiles-"));
    const { createProfileFromPreset } = await loadProfilesModule();
    const path = await createProfileFromPreset("service", "my-service", root);
    const original = await readFile(path, "utf8");

    await expect(createProfileFromPreset("library", "my-service", root))
      .rejects.toThrow(/already exists/);
    expect(await readFile(path, "utf8")).toBe(original);
    expect(original).toContain("name: my-service");
    expect(original).toContain("preset: service");
  });
});
