import { describe, expect, test } from "vitest";
import type { ScaffoldProfile } from "../src/schema.js";

async function loadPlanner() {
  return import("../src/planning.js");
}

function profile(overrides: Partial<ScaffoldProfile> = {}): ScaffoldProfile {
  return {
    schema_version: 1,
    name: "default",
    preset: "library",
    package_manager: "pnpm",
    package_manager_version: "11.24.0",
    module: "esm",
    build: "tsup",
    quality: "biome",
    tests: "vitest",
    runtime_validation: "none",
    http: "none",
    logging: "none",
    hooks: "lefthook",
    commit_lint: "commitlint",
    ci: "github-actions",
    publishing: "npm",
    workspace: "none",
    workspace_members: [],
    secret_scan: "gitleaks",
    duplication: "jscpd",
    framework: "none",
    license: "apache-2.0",
    install_dependencies: false,
    run_quality_gates: false,
    initialize_git: false,
    default_author: "Example Maintainer",
    project: {
      name: "",
      description: "",
      author: "",
      repository_url: "",
    },
    package_versions: {
      typescript: "^5.9.3",
      tsup: "^8.5.1",
      vitest: "^4.1.11",
      "@biomejs/biome": "^2.5.10",
      lefthook: "^2.1.10",
      jscpd: "^4.0.8",
    },
    extra_dependencies: [],
    extra_dev_dependencies: [],
    extra_scripts: {},
    ci_commands: ["pnpm lint", "pnpm test", "pnpm build"],
    ...overrides,
  };
}

describe("provider planning", () => {
  test("composes a publishable library without package-specific planner branches", async () => {
    const { createGenerationPlan } = await loadPlanner();
    const plan = createGenerationPlan(profile(), {
      name: "example-library",
      description: "Example TypeScript library.",
      author: "Example Maintainer",
    });

    expect(plan.packageJson.packageManager).toBe("pnpm@11.24.0");
    expect(plan.packageJson.type).toBe("module");
    expect(plan.packageJson.engines).toEqual({ node: ">=24" });
    expect(plan.files.get(".node-version")).toBe("24\n");
    expect(plan.files.get(".gitignore")).toContain(".pnp.*");
    expect(JSON.parse(plan.files.get("biome.json")!)).toMatchObject({
      linter: { rules: { preset: "recommended" } },
    });
    expect(JSON.parse(plan.files.get("tsconfig.json")!)).toMatchObject({
      compilerOptions: { types: ["node"] },
      include: ["src", "test", "*.config.*"],
    });
    expect(JSON.parse(plan.files.get("tsconfig.build.json")!)).toMatchObject({
      extends: "./tsconfig.json",
      compilerOptions: { rootDir: "src", outDir: "dist" },
      include: ["src"],
    });
    expect(plan.files.get("README.md")).toContain("HTTP: none");
    expect(plan.packageJson.scripts).toMatchObject({
      build: "tsup",
      lint: "biome check --error-on-warnings .",
      test: "vitest run",
      duplication: "jscpd src",
      secrets: "gitleaks dir . --no-banner",
    });
    expect(plan.packageJson.devDependencies).toMatchObject({
      "@biomejs/biome": "^2.5.10",
      lefthook: "^2.1.10",
      tsup: "^8.5.1",
      typescript: "^5.9.3",
      vitest: "^4.1.11",
    });
    expect([...plan.files.keys()]).toEqual(expect.arrayContaining([
      ".github/workflows/ci.yml",
      ".gitignore",
      ".jscpd.json",
      "CONTRIBUTING.md",
      "LICENSE",
      "README.md",
      "biome.json",
      "lefthook.yml",
      "src/index.ts",
      "test/index.test.ts",
      "tsconfig.json",
      "tsup.config.ts",
      "vitest.config.mts",
    ]));
  });

  test("composes a Fastify service integration", async () => {
    const { createGenerationPlan } = await loadPlanner();
    const plan = createGenerationPlan(profile({
      preset: "service",
      package_manager: "npm",
      package_manager_version: "11.17.0",
      build: "tsc",
      quality: "eslint-prettier",
      runtime_validation: "zod",
      http: "fastify",
      logging: "pino",
      hooks: "husky-lint-staged",
      ci: "gitlab-ci",
      publishing: "none",
      secret_scan: "none",
      duplication: "none",
      package_versions: {},
      ci_commands: ["npm run lint", "npm test", "npm run build"],
    }), {
      name: "catalog-api",
      description: "Catalog API.",
      author: "Example Maintainer",
    });

    expect(plan.packageJson.dependencies).toMatchObject({
      fastify: expect.any(String),
      pino: expect.any(String),
      zod: expect.any(String),
    });
    expect(plan.packageJson.devDependencies).toMatchObject({
      eslint: expect.any(String),
      husky: expect.any(String),
      prettier: expect.any(String),
    });
    expect([...plan.files.keys()]).toEqual(expect.arrayContaining([
      ".gitlab-ci.yml",
      ".husky/pre-commit",
      ".husky/pre-push",
      "src/app.ts",
      "src/server.ts",
      "test/server.test.ts",
    ]));
    expect(plan.files.get("src/server.ts")).toContain("buildApp");
    expect(plan.files.get("test/server.test.ts")).toContain("app.inject");
    expect(plan.files.has(".github/workflows/ci.yml")).toBe(false);
    expect(plan.files.get(".gitlab-ci.yml")).toContain("image: node:24");
  });

  test("none providers leave no provider artifacts", async () => {
    const { createGenerationPlan } = await loadPlanner();
    const plan = createGenerationPlan(profile({
      build: "tsc",
      quality: "none",
      tests: "none",
      hooks: "none",
      commit_lint: "none",
      ci: "none",
      publishing: "none",
      secret_scan: "none",
      duplication: "none",
      package_versions: {},
      ci_commands: [],
    }), {
      name: "plain-library",
      description: "Plain library.",
      author: "",
    });

    expect(plan.packageJson.devDependencies).not.toHaveProperty("vitest");
    expect(plan.packageJson.devDependencies).not.toHaveProperty("@biomejs/biome");
    expect([...plan.files.keys()]).not.toEqual(expect.arrayContaining([
      ".github/workflows/ci.yml",
      ".gitlab-ci.yml",
      "biome.json",
      "eslint.config.mjs",
      "vitest.config.mts",
    ]));
    expect(plan.files.get("README.md")).not.toContain("pnpm dev");
    expect(plan.files.get("README.md")).not.toContain("pnpm lint");
    expect(plan.files.get("README.md")).not.toContain("pnpm test");
  });

  test("rejects HTTP providers outside a service preset", async () => {
    const { createGenerationPlan } = await loadPlanner();

    expect(() => createGenerationPlan(profile({ http: "fastify" }), {
      name: "bad-library",
      description: "Invalid combination.",
      author: "",
    })).toThrow(/HTTP providers require the service preset/);
  });

  test("requires an HTTP provider for the service preset", async () => {
    const { createGenerationPlan } = await loadPlanner();

    expect(() => createGenerationPlan(profile({
      preset: "service",
      http: "none",
      build: "tsc",
      publishing: "none",
    }), {
      name: "empty-service",
      description: "Invalid empty service.",
      author: "",
    })).toThrow(/service preset requires an HTTP provider/i);
  });

  test("rejects quality gates when dependencies are not installed", async () => {
    const { createGenerationPlan } = await loadPlanner();

    expect(() => createGenerationPlan(profile({
      install_dependencies: false,
      run_quality_gates: true,
    }), {
      name: "missing-dependencies",
      description: "Invalid execution controls.",
      author: "",
    })).toThrow(/quality gates require dependency installation/i);
  });

  test("rejects Vite outside a private library preset", async () => {
    const { createGenerationPlan } = await loadPlanner();
    const project = {
      name: "vite-app",
      description: "Vite application.",
      author: "",
    };

    expect(() => createGenerationPlan(profile({
      preset: "cli",
      framework: "vite-react",
      build: "framework-owned",
      publishing: "none",
      hooks: "none",
      commit_lint: "none",
    }), project)).toThrow(/Vite React.*library preset/i);
    expect(() => createGenerationPlan(profile({
      framework: "vite-react",
      build: "framework-owned",
      publishing: "npm",
      hooks: "none",
      commit_lint: "none",
    }), project)).toThrow(/Vite React.*publishing disabled/i);
  });

  test("rejects an invalid package name", async () => {
    const { createGenerationPlan } = await loadPlanner();

    expect(() => createGenerationPlan(profile(), {
      name: "Invalid Package Name",
      description: "Invalid package.",
      author: "",
    })).toThrow(/package name/);
  });

  test("rejects TypeScript 6 with tsup declaration generation", async () => {
    const { createGenerationPlan } = await loadPlanner();

    expect(() => createGenerationPlan(profile({
      package_versions: { typescript: "^6.0.3" },
    }), {
      name: "incompatible-library",
      description: "Incompatible library.",
      author: "",
    })).toThrow(/tsup.*TypeScript 5\.9/i);
  });

  test("omits licence references when no licence is selected", async () => {
    const { createGenerationPlan } = await loadPlanner();
    const plan = createGenerationPlan(profile({ license: "none" }), {
      name: "unlicensed-library",
      description: "Unlicensed library.",
      author: "",
    });

    expect(plan.files.has("LICENSE")).toBe(false);
    expect(plan.files.get("README.md")).not.toContain("[LICENSE](LICENSE)");
    expect(plan.files.get("CONTRIBUTING.md")).not.toContain("repository licence");
    expect(plan.packageJson.files).not.toContain("LICENSE");
  });

  test("renders an attributed MIT licence without template placeholders", async () => {
    const { createGenerationPlan } = await loadPlanner();
    const plan = createGenerationPlan(profile({ license: "mit" }), {
      name: "mit-library",
      description: "MIT library.",
      author: "Example Maintainer",
    });
    const license = plan.files.get("LICENSE");

    expect(license).toMatch(/Copyright \(c\) \d{4} Example Maintainer/);
    expect(license).not.toContain("<year>");
    expect(license).not.toContain("<copyright holders>");
  });

  test("requires an author for an MIT licence", async () => {
    const { createGenerationPlan } = await loadPlanner();

    expect(() => createGenerationPlan(profile({ license: "mit" }), {
      name: "anonymous-mit-library",
      description: "MIT library.",
      author: "",
    })).toThrow(/MIT licence requires an author/);
  });
});
