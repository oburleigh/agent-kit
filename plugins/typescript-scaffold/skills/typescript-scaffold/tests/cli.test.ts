import { access, mkdir, mkdtemp, readFile, writeFile } from "node:fs/promises";
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

    const result = await main(["--profile", profilePath, "--target", target]);

    expect(result).toBe(target);
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

  test("plans a repository without creating a profile or target", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-plan-"));
    const config = join(root, "config");
    const target = join(root, "planned-library");
    const { main } = await loadCli();

    const result = await main(
      ["--profile", "library:efficient", "--target", target, "--plan"],
      { AGENT_KIT_CONFIG_DIR: config },
    );

    expect(typeof result).toBe("string");
    expect(JSON.parse(String(result))).toEqual({
        schema_version: 1,
        target,
        preset: "library",
        project: {
          name: "planned-library",
          description: "planned-library TypeScript library.",
          author: "",
          repository_url: "",
        },
        selected_providers: {
          build: "tsup",
          ci: "github-actions",
          commit_lint: "commitlint",
          duplication: "jscpd",
          hooks: "lefthook",
          license: "apache-2.0",
          module: "esm",
          package_manager: "pnpm@11.24.0",
          publishing: "npm",
          quality: "biome",
          secret_scan: "gitleaks",
          tests: "vitest",
        },
        disabled_providers: [
          "framework",
          "http",
          "logging",
          "runtime_validation",
          "workspace",
        ],
        workspace_members: [],
        quality_gates: [
          "pnpm lint",
          "pnpm typecheck",
          "pnpm test",
          "pnpm build",
          "pnpm duplication",
          "pnpm secrets",
        ],
        execution: {
          install_dependencies: true,
          run_quality_gates: true,
          initialize_git: true,
        },
    });
    await expect(access(target)).rejects.toMatchObject({ code: "ENOENT" });
    await expect(access(config)).rejects.toMatchObject({ code: "ENOENT" });
  });

  test("applies persistent profile name validation while planning", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-plan-name-"));
    const { main } = await loadCli();

    await expect(main(
      ["--profile", "library:bad name", "--target", join(root, "target"), "--plan"],
      { AGENT_KIT_CONFIG_DIR: join(root, "config") },
    )).rejects.toThrow(/Profile names may contain/);
  });

  test("plans from an existing legacy profile name accepted by generation", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-plan-legacy-name-"));
    const config = join(root, "config");
    const profileDirectory = join(config, "scaffolds", "typescript");
    const profilePath = join(profileDirectory, "legacy name.yaml");
    const profile = await loadBundledPreset("library");
    await mkdir(profileDirectory, { recursive: true });
    await writeFile(profilePath, stringify({ ...profile, name: "legacy name" }));
    const { main } = await loadCli();

    const result = await main(
      ["--profile", "library:legacy name", "--target", join(root, "target"), "--plan"],
      { AGENT_KIT_CONFIG_DIR: config },
    );

    expect(JSON.parse(result)).toMatchObject({ preset: "library" });
  });
});
