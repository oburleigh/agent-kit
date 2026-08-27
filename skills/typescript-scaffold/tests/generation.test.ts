import { access, mkdtemp, mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, test } from "vitest";
import type { ScaffoldProfile } from "../src/schema.js";
import type { SignalRuntime } from "../src/generate.js";

async function loadGenerator() {
  return import("../src/generate.js");
}

function profile(overrides: Partial<ScaffoldProfile> = {}): ScaffoldProfile {
  return {
    schema_version: 1,
    name: "render-test",
    preset: "library",
    package_manager: "npm",
    package_manager_version: "11.17.0",
    module: "esm",
    build: "tsc",
    quality: "biome",
    tests: "vitest",
    runtime_validation: "none",
    http: "none",
    logging: "none",
    hooks: "none",
    commit_lint: "none",
    ci: "github-actions",
    publishing: "npm",
    workspace: "none",
    workspace_members: [],
    secret_scan: "none",
    duplication: "none",
    framework: "none",
    license: "apache-2.0",
    install_dependencies: false,
    run_quality_gates: false,
    initialize_git: false,
    default_author: "Example Maintainer",
    project: {
      name: "rendered-library",
      description: "A rendered TypeScript library.",
      author: "Example Maintainer",
      repository_url: "",
    },
    package_versions: {},
    extra_dependencies: [],
    extra_dev_dependencies: [],
    extra_scripts: {},
    ci_commands: ["npm run lint", "npm test", "npm run build"],
    ...overrides,
  };
}

describe("repository generation", () => {
  test("renders a complete repository into an absent target", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-generate-"));
    const target = join(root, "rendered-library");
    const { generateRepository } = await loadGenerator();

    await generateRepository(profile(), target);

    const packageJson = JSON.parse(await readFile(join(target, "package.json"), "utf8"));
    expect(packageJson.name).toBe("rendered-library");
    expect(packageJson.license).toBe("Apache-2.0");
    expect(await readFile(join(target, "README.md"), "utf8"))
      .toContain("# rendered-library");
    await expect(access(join(target, "CONTRIBUTING.md"))).resolves.toBeUndefined();
    await expect(access(join(target, "AGENTS.md"))).resolves.toBeUndefined();
    await expect(access(join(target, "CLAUDE.md"))).resolves.toBeUndefined();
    await expect(access(join(target, ".gitignore"))).resolves.toBeUndefined();
    await expect(access(join(target, "LICENSE"))).resolves.toBeUndefined();
    expect(await readFile(join(target, "AGENTS.md"), "utf8"))
      .toContain("Prefer a maintained package");
  });

  test("installs, checks, and initializes Git in that order", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-order-"));
    const target = join(root, "ordered");
    const commands: string[] = [];
    const { generateRepository } = await loadGenerator();

    await generateRepository(profile({
      install_dependencies: true,
      run_quality_gates: true,
      initialize_git: true,
      quality: "none",
      tests: "none",
      ci: "none",
    }), target, {
      runCommand: async (command, args) => {
        commands.push([command, ...args].join(" "));
      },
    });

    expect(commands).toEqual([
      "npm install --ignore-scripts",
      "npm run typecheck",
      "npm run build",
      "git init --initial-branch=main",
    ]);
  });

  test("formats generated files with the selected quality provider before gates", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-format-"));
    const target = join(root, "formatted");
    const commands: string[] = [];
    const { generateRepository } = await loadGenerator();

    await generateRepository(profile({
      install_dependencies: true,
      run_quality_gates: false,
      initialize_git: false,
      tests: "none",
      ci: "none",
    }), target, {
      runCommand: async (command, args) => {
        commands.push([command, ...args].join(" "));
      },
    });

    expect(commands).toEqual([
      "npm install --ignore-scripts",
      "npm run format",
    ]);
  });

  test("uses Yarn's lifecycle-safe install mode", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-yarn-install-"));
    const target = join(root, "yarn-project");
    const commands: string[] = [];
    const { generateRepository } = await loadGenerator();

    await generateRepository(profile({
      package_manager: "yarn",
      package_manager_version: "4.18.0",
      install_dependencies: true,
      quality: "none",
      tests: "none",
      ci: "none",
    }), target, {
      runCommand: async (command, args) => {
        commands.push([command, ...args].join(" "));
      },
    });

    expect(commands[0]).toBe("yarn install --mode=skip-build");
  });

  test("removes a generator-owned target after a failed gate", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-failure-"));
    const target = join(root, "failed");
    const { generateRepository } = await loadGenerator();

    await expect(generateRepository(profile({
      install_dependencies: true,
      run_quality_gates: true,
      quality: "none",
      tests: "none",
      ci: "none",
    }), target, {
      runCommand: async (command, args) => {
        if ([command, ...args].join(" ") === "npm run build") {
          throw new Error("build failed");
        }
      },
    })).rejects.toThrow(/build failed/);
    await expect(access(target)).rejects.toMatchObject({ code: "ENOENT" });
  });

  test("removes staging output after dependency installation fails", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-install-failure-"));
    const target = join(root, "failed-install");
    const { generateRepository } = await loadGenerator();

    await expect(generateRepository(profile({
      install_dependencies: true,
      ci: "none",
    }), target, {
      runCommand: async () => {
        throw new Error("install failed");
      },
    })).rejects.toThrow(/install failed/);
    await expect(access(target)).rejects.toMatchObject({ code: "ENOENT" });
    expect(await readdir(root)).toEqual([]);
  });

  test("refuses an existing empty target without altering it", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-empty-"));
    const target = join(root, "empty");
    await mkdir(target);
    const { generateRepository } = await loadGenerator();

    await expect(generateRepository(profile(), target)).rejects.toThrow(/already exists/);
    expect(await readdir(target)).toEqual([]);
  });

  test("reports a missing target parent without leaking the staging path", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-parent-"));
    const target = join(root, "missing", "nested-project");
    const { generateRepository } = await loadGenerator();

    await expect(generateRepository(profile(), target))
      .rejects.toThrow(/Parent directory .* does not exist/);
  });

  test("removes staging output on an interruptible signal", async () => {
    const target = await mkdtemp(join(tmpdir(), "agent-kit-signal-cleanup-"));
    await writeFile(join(target, "partial.txt"), "partial output\n");
    const listeners = new Map<string, () => void>();
    const terminated: string[] = [];
    const runtime: SignalRuntime = {
      once(signal, listener) {
        listeners.set(signal, listener);
      },
      off(signal) {
        listeners.delete(signal);
      },
      terminate(signal) {
        terminated.push(signal);
      },
    };
    const { registerSignalCleanup } = await import("../src/generate.js");
    registerSignalCleanup(target, runtime);

    listeners.get("SIGTERM")?.();
    await expect.poll(async () => access(target).then(() => true, () => false)).toBe(false);
    expect(terminated).toEqual(["SIGTERM"]);
  });

  test("rejects a package-manager version mismatch", async () => {
    const { assertPackageManagerVersion } = await import("../src/generate.js");

    await expect(assertPackageManagerVersion(
      "npm",
      "11.17.0",
      "/tmp",
      async () => "11.12.1\n",
    ))
      .rejects.toThrow(/Expected npm 11\.17\.0.*found 11\.12\.1/);
  });
});
