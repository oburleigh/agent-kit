import { mkdtemp, readFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { parse, stringify } from "yaml";
import { describe, expect, test } from "vitest";
import { loadProfileText } from "../src/profile.js";

async function loadProfilesModule() {
  return import("../src/profiles.js");
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

  test("materializes package-manager policy without version pins in a preset template", async () => {
    const template = parse(await readFile("config/presets/service.yaml", "utf8"));
    delete template.package_manager_version;
    delete template.package_versions;
    const { loadBundledPresetText } = await loadProfilesModule();

    const profile = loadBundledPresetText(stringify(template));

    expect(profile.package_manager_version).toBe("11.17.0");
    expect(profile.package_versions).toEqual({});
  });

  test("rejects a package manager major without an exact version", async () => {
    const { loadBundledPreset } = await loadProfilesModule();
    const profile = await loadBundledPreset("service");

    expect(() => loadProfileText(stringify({ ...profile, package_manager_version: "11" })))
      .toThrow(/exact semantic version/);
  });

  test.each(["cli", "workspace"] as const)(
    "gives the %s preset a working CI default",
    async (preset) => {
      const { loadBundledPreset } = await loadProfilesModule();

      expect((await loadBundledPreset(preset)).ci).toBe("github-actions");
    },
  );
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
