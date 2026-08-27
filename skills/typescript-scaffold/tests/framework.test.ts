import { mkdtemp, readFile, writeFile, mkdir } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, test } from "vitest";
import type { ScaffoldProfile } from "../src/schema.js";
import { generateRepository } from "../src/generate.js";
import { mergeFrameworkOutput } from "../src/framework-generators.js";
import { createGenerationPlan } from "../src/planning.js";

function viteProfile(): ScaffoldProfile {
  return {
    schema_version: 1,
    name: "vite-react",
    preset: "library",
    package_manager: "npm",
    package_manager_version: "11.17.0",
    module: "esm",
    build: "framework-owned",
    quality: "none",
    tests: "none",
    runtime_validation: "none",
    http: "none",
    logging: "none",
    hooks: "none",
    commit_lint: "none",
    ci: "none",
    publishing: "none",
    workspace: "none",
    workspace_members: [],
    secret_scan: "none",
    duplication: "none",
    framework: "vite-react",
    license: "apache-2.0",
    install_dependencies: false,
    run_quality_gates: false,
    initialize_git: false,
    default_author: "",
    project: {
      name: "web-app",
      description: "Example web app.",
      author: "",
      repository_url: "",
    },
    package_versions: { "create-vite": "9.2.0" },
    extra_dependencies: [],
    extra_dev_dependencies: [],
    extra_scripts: {},
    ci_commands: [],
  };
}

describe("official framework delegation", () => {
  test("rejects a Vite quality overlay before invoking the official generator", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-vite-quality-"));
    const target = join(root, "web-app");
    const profile = viteProfile();
    profile.quality = "biome";
    const commands: string[] = [];

    await expect(generateRepository(profile, target, {
      runCommand: async (command, args) => {
        commands.push([command, ...args].join(" "));
      },
    })).rejects.toThrow(/Vite React.*quality.*none/i);
    expect(commands).toEqual([]);
  });

  test("generates React-aware Vitest files instead of the library sample", () => {
    const profile = viteProfile();
    profile.tests = "vitest";
    const plan = createGenerationPlan(profile, {
      name: "web-app",
      description: "Example web app.",
      author: "",
    });

    expect(plan.files.has("test/index.test.ts")).toBe(false);
    expect(plan.files.get("src/App.test.tsx")).toContain("render(<App />)");
    expect(plan.files.get("vitest.config.ts")).toContain("@vitejs/plugin-react");
    expect(plan.packageJson.devDependencies).toMatchObject({
      "@testing-library/react": expect.any(String),
      jsdom: expect.any(String),
    });
  });

  test("preserves Vite source and commands while applying the agent-kit overlay", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-vite-"));
    const target = join(root, "web-app");
    const commands: string[] = [];

    await generateRepository(viteProfile(), target, {
      runCommand: async (command, args, options) => {
        commands.push([command, ...args].join(" "));
        if (args[0]?.startsWith("create")) {
          await mkdir(join(options.cwd, "src"), { recursive: true });
          await writeFile(join(options.cwd, "package.json"), JSON.stringify({
            name: "web-app",
            private: true,
            type: "module",
            scripts: { dev: "vite", build: "tsc -b && vite build" },
            dependencies: { react: "^19.0.0", "react-dom": "^19.0.0" },
            devDependencies: { vite: "^7.0.0" },
          }));
          await writeFile(join(options.cwd, "README.md"), "Vite default\n");
          await writeFile(join(options.cwd, "src/App.tsx"), "export default function App() { return <main>Hello</main>; }\n");
        }
      },
    });

    expect(commands).toEqual(["npm create vite@9.2.0 . -- --template react-ts"]);
    expect(await readFile(join(target, "src/App.tsx"), "utf8")).toContain("<main>Hello</main>");
    const packageJson = JSON.parse(await readFile(join(target, "package.json"), "utf8"));
    expect(packageJson.scripts.dev).toBe("vite");
    expect(packageJson.dependencies.react).toBe("^19.0.0");
    expect(packageJson).not.toHaveProperty("exports");
    expect(await readFile(join(target, ".gitignore"), "utf8")).toContain("dist-ssr/");
    expect(await readFile(join(target, "README.md"), "utf8")).toContain("# web-app");
  });

  test("runs official framework checks after merging package scripts", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-vite-gates-"));
    const target = join(root, "web-app");
    const commands: string[] = [];
    const profile = viteProfile();
    profile.install_dependencies = true;
    profile.run_quality_gates = true;

    await generateRepository(profile, target, {
      runCommand: async (command, args, options) => {
        commands.push([command, ...args].join(" "));
        if (args[0]?.startsWith("create")) {
          await writeFile(join(options.cwd, "package.json"), JSON.stringify({
            name: "web-app",
            private: true,
            type: "module",
            scripts: { build: "vite build" },
            dependencies: {},
            devDependencies: {},
          }));
        }
      },
    });

    expect(commands).toEqual([
      "npm create vite@9.2.0 . -- --template react-ts",
      "npm install --ignore-scripts",
      "npm run build",
    ]);
  });

  test("uses the selected package manager for framework delegation", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-vite-manager-"));
    const target = join(root, "web-app");
    const profile = viteProfile();
    profile.package_manager = "pnpm";
    profile.package_manager_version = "11.24.0";
    const commands: string[] = [];

    await generateRepository(profile, target, {
      runCommand: async (command, args, options) => {
        commands.push([command, ...args].join(" "));
        if (args[0] === "create") {
          await writeFile(join(options.cwd, "package.json"), JSON.stringify({
            name: "web-app",
            scripts: {},
            dependencies: {},
            devDependencies: {},
          }));
        }
      },
    });

    expect(commands).toEqual(["pnpm create vite@9.2.0 . --template react-ts"]);
  });

  test("verifies the package manager before running a framework generator", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-vite-version-"));
    const target = join(root, "web-app");
    const commands: string[] = [];

    await expect(generateRepository(viteProfile(), target, {
      runCommand: async (command, args) => {
        commands.push([command, ...args].join(" "));
      },
      readPackageManagerVersion: async () => "11.12.1",
    })).rejects.toThrow(/Expected npm 11\.17\.0/);
    expect(commands).toEqual([]);
  });

  test("rejects framework dependencies assigned to the profile's dev bucket", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-vite-dependency-"));
    const target = join(root, "web-app");
    const profile = viteProfile();
    profile.extra_dev_dependencies = [{ name: "react", version: "^19.0.0" }];

    await expect(generateRepository(profile, target, {
      runCommand: async (_command, args, options) => {
        if (args[0]?.startsWith("create")) {
          await writeFile(join(options.cwd, "package.json"), JSON.stringify({
            name: "web-app",
            scripts: {},
            dependencies: { react: "^19.0.0" },
            devDependencies: {},
          }));
        }
      },
    })).rejects.toThrow(/react.*dependencies.*devDependencies/i);
  });

  test("rejects profile overrides of official framework commands", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-vite-conflict-"));
    const target = join(root, "web-app");
    const profile = viteProfile();
    profile.extra_scripts = { dev: "custom-dev-server" };

    await expect(generateRepository(profile, target, {
      runCommand: async (_command, args, options) => {
        if (args[0]?.startsWith("create")) {
          await writeFile(join(options.cwd, "package.json"), JSON.stringify({
            name: "web-app",
            private: true,
            type: "module",
            scripts: { dev: "vite" },
            dependencies: {},
            devDependencies: {},
          }));
        }
      },
    })).rejects.toThrow(/conflicts on script dev/);
  });

  test("validates overlay paths before deleting framework files", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-vite-path-"));
    const target = join(root, "web-app");
    const outside = join(root, "outside.txt");
    await mkdir(target);
    await writeFile(outside, "keep me\n");
    await writeFile(join(target, "package.json"), JSON.stringify({
      name: "web-app",
      scripts: {},
      dependencies: {},
      devDependencies: {},
    }));
    const profile = viteProfile();
    const plan = createGenerationPlan(profile, {
      name: "web-app",
      description: "Example web app.",
      author: "",
    });
    plan.files.set("../outside.txt", "delete me\n");

    await expect(mergeFrameworkOutput(plan, target)).rejects.toThrow(/escapes the target/);
    expect(await readFile(outside, "utf8")).toBe("keep me\n");
  });
});
