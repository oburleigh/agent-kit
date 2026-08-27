import { access, mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { stringify } from "yaml";
import { describe, expect, test } from "vitest";
import { loadBundledPreset } from "../src/profiles.js";

async function loadCli() {
  return import("../src/cli.js");
}

describe("generator CLI", () => {
  test("creates a repository from profile and target arguments", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-cli-"));
    const profilePath = join(root, "profile.yaml");
    const target = join(root, "cli-output");
    const preset = await loadBundledPreset("library");
    await writeFile(profilePath, stringify({
      ...preset,
      install_dependencies: false,
      run_quality_gates: false,
      initialize_git: false,
      project: {
        ...preset.project,
        name: "cli-output",
        description: "Generated through the internal CLI.",
      },
    }));
    const { main } = await loadCli();

    await main(["--profile", profilePath, "--target", target]);

    await expect(access(join(target, "README.md"))).resolves.toBeUndefined();
  });

  test("requires both supported arguments", async () => {
    const { main } = await loadCli();

    await expect(main(["--profile", "profile.yaml"]))
      .rejects.toThrow(/--profile and --target are required/);
  });

  test("creates a reusable named profile from a preset selector", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-profile-selector-"));
    const { resolveProfileArgument } = await loadCli();

    const profilePath = await resolveProfileArgument("service:backend", {
      AGENT_KIT_CONFIG_DIR: root,
    });

    expect(profilePath).toBe(join(root, "scaffolds", "typescript", "backend.yaml"));
    expect(await readFile(profilePath, "utf8")).toContain("preset: service");
  });
});
