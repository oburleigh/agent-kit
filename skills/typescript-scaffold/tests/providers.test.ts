import { describe, expect, test } from "vitest";
import { parse } from "yaml";
import { providerCatalog } from "../providers/catalog.js";
import { createGenerationPlan } from "../src/planning.js";
import type { ScaffoldProfile } from "../src/schema.js";

function baseProfile(overrides: Partial<ScaffoldProfile> = {}): ScaffoldProfile {
  return {
    schema_version: 1,
    name: "provider-test",
    preset: "service",
    package_manager: "npm",
    package_manager_version: "11.17.0",
    module: "esm",
    build: "tsc",
    quality: "none",
    tests: "none",
    runtime_validation: "none",
    http: "fastify",
    logging: "none",
    hooks: "none",
    ci: "none",
    publishing: "none",
    workspace: "none",
    secret_scan: "none",
    duplication: "none",
    framework: "none",
    license: "apache-2.0",
    install_dependencies: false,
    run_quality_gates: false,
    initialize_git: false,
    default_author: "",
    project: { name: "", description: "", author: "", repository_url: "" },
    package_versions: {},
    extra_dependencies: [],
    extra_dev_dependencies: [],
    extra_scripts: {},
    ci_commands: [],
    ...overrides,
  };
}

function plan(overrides: Partial<ScaffoldProfile> = {}) {
  return createGenerationPlan(baseProfile(overrides), {
    name: "provider-test",
    description: "Provider test.",
    author: "",
  });
}

describe("first-class provider catalog", () => {
  test("registers every advertised provider", () => {
    expect(providerCatalog.map(({ id }) => id)).toEqual(expect.arrayContaining([
      "build-tsc",
      "build-tsup",
      "build-framework",
      "quality-biome",
      "quality-eslint-prettier",
      "tests-vitest",
      "tests-node",
      "tests-jest",
      "validation-zod",
      "validation-valibot",
      "http-fastify",
      "http-express",
      "http-hono",
      "http-nestjs",
      "logging-pino",
      "logging-winston",
      "hooks-lefthook",
      "hooks-husky-lint-staged",
      "ci-github-actions",
      "ci-gitlab",
      "publishing-npm",
      "workspace-turbo",
      "workspace-nx",
      "secret-gitleaks",
      "duplication-jscpd",
    ]));
  });

  test.each([
    ["express", "express", "src/server.ts"],
    ["hono", "hono", "src/server.ts"],
    ["nestjs", "@nestjs/core", "src/app.module.ts"],
  ] as const)("plans the %s HTTP provider", (http, dependency, file) => {
    const result = plan({ http, tests: "vitest" });
    expect(result.packageJson.dependencies).toHaveProperty(dependency);
    expect(result.files.has(file)).toBe(true);
    expect(result.files.has("test/server.test.ts")).toBe(true);
  });

  test("plans a buildable and tested CLI entry point", () => {
    const result = plan({
      preset: "cli",
      http: "none",
      build: "tsup",
      tests: "node-test",
      package_versions: { typescript: "^5.9.3" },
    });

    expect(result.files.get("tsup.config.ts")).toContain('entry: ["src/cli.ts"]');
    expect(result.files.get("test/cli.test.ts")).toContain("greeting");
    expect(result.files.get("src/cli.ts")).toContain("export function greeting");
  });

  test("enables legacy decorators for NestJS", () => {
    const result = plan({ http: "nestjs" });
    const tsconfig = JSON.parse(result.files.get("tsconfig.json")!);

    expect(tsconfig.compilerOptions).toMatchObject({
      experimentalDecorators: true,
      emitDecoratorMetadata: true,
    });
  });

  test("rejects Node type stripping for decorated NestJS source", () => {
    expect(() => plan({ http: "nestjs", tests: "node-test" }))
      .toThrow(/NestJS.*Vitest or Jest/);
  });

  test("rejects integrations not wired into the selected HTTP provider", () => {
    expect(() => plan({ http: "express", runtime_validation: "zod" }))
      .toThrow(/runtime validation.*Fastify/i);
    expect(() => plan({ http: "hono", logging: "pino" }))
      .toThrow(/logging.*Fastify/i);
  });

  test("plans Valibot and Winston source integrations", () => {
    const result = plan({ runtime_validation: "valibot", logging: "winston" });
    expect(result.packageJson.dependencies).toMatchObject({
      valibot: expect.any(String),
      winston: expect.any(String),
    });
    expect(result.files.get("src/app.ts")).toContain("from \"valibot\"");
    expect(result.files.get("src/logger.ts")).toContain("from \"winston\"");
  });

  test.each([
    ["node-test", "node --test --experimental-strip-types test/*.test.ts"],
    ["jest", "jest"],
    ["vitest", "vitest run"],
  ] as const)("plans the %s test provider", (tests, command) => {
    expect(plan({ tests }).packageJson.scripts.test).toBe(command);
  });

  test("uses SWC rather than a TypeScript-version-bound Jest transformer", () => {
    const result = plan({ tests: "jest" });

    expect(result.packageJson.devDependencies).toHaveProperty("@swc/jest");
    expect(result.packageJson.devDependencies).toHaveProperty("@swc/core");
    expect(result.packageJson.devDependencies).not.toHaveProperty("ts-jest");
    expect(result.files.get("jest.config.mjs")).toContain("@swc/jest");
  });

  test.each(["turbo", "nx"] as const)("plans the %s workspace provider", (workspace) => {
    const result = plan({
      preset: "workspace",
      workspace,
      http: "none",
      build: "tsc",
    });
    expect(result.packageJson.devDependencies).toHaveProperty(workspace);
    expect(result.files.has(`${workspace}.json`)).toBe(true);
    expect(result.files.get(".gitignore")).toContain(`.${workspace}/`);
  });

  test("honors extra packages and scripts without inventing files", () => {
    const result = plan({
      extra_dependencies: [{ name: "nanoid", version: "^5.1.0" }],
      extra_dev_dependencies: [{ name: "publint", version: "^0.3.0" }],
      extra_scripts: { check: "npm run typecheck" },
    });
    expect(result.packageJson.dependencies.nanoid).toBe("^5.1.0");
    expect(result.packageJson.devDependencies.publint).toBe("^0.3.0");
    expect(result.packageJson.scripts.check).toBe("npm run typecheck");
    expect([...result.files.keys()].some((path) => path.includes("nanoid"))).toBe(false);
  });

  test("keeps an extra dependency's explicit version", () => {
    const result = plan({
      package_versions: { nanoid: "^4.0.0" },
      extra_dependencies: [{ name: "nanoid", version: "^5.1.0" }],
    });

    expect(result.packageJson.dependencies.nanoid).toBe("^5.1.0");
  });

  test("rejects a package assigned to both dependency buckets", () => {
    expect(() => plan({
      runtime_validation: "zod",
      extra_dev_dependencies: [{ name: "zod", version: "^4.4.3" }],
    })).toThrow(/zod.*dependencies.*devDependencies/i);
  });

  test("bootstraps pnpm in GitHub Actions", () => {
    const workflow = plan({
      ci: "github-actions",
      package_manager: "pnpm",
      package_manager_version: "11.24.0",
    }).files.get(".github/workflows/ci.yml");

    const parsed = parse(workflow!);
    expect(parsed.jobs.test.steps).toEqual(expect.arrayContaining([
      { uses: "pnpm/action-setup@v4", with: { version: "11.24.0" } },
      {
        uses: "actions/setup-node@v4",
        with: { "node-version-file": ".node-version", cache: "pnpm" },
      },
    ]));
  });

  test("bootstraps Bun without asking setup-node to cache it", () => {
    const workflow = plan({
      ci: "github-actions",
      package_manager: "bun",
      package_manager_version: "1.3.14",
    }).files.get(".github/workflows/ci.yml");

    const parsed = parse(workflow!);
    expect(parsed.jobs.test.steps).toEqual(expect.arrayContaining([
      { uses: "oven-sh/setup-bun@v2", with: { "bun-version": "1.3.14" } },
    ]));
    expect(workflow).not.toContain("cache: bun");
  });

  test("derives standard CI checks from the selected package manager", () => {
    const workflow = plan({
      ci: "github-actions",
      package_manager: "bun",
      package_manager_version: "1.3.14",
      quality: "biome",
      tests: "vitest",
      ci_commands: [],
    }).files.get(".github/workflows/ci.yml");
    const runs = parse(workflow!).jobs.test.steps
      .filter((step: { run?: string }) => step.run)
      .map((step: { run: string }) => step.run);

    expect(runs).toEqual(expect.arrayContaining([
      "bun run lint",
      "bun run typecheck",
      "bun run test",
      "bun run build",
    ]));
    expect(runs.some((run: string) => run.startsWith("npm ") || run.startsWith("pnpm ")))
      .toBe(false);
  });

  test("bootstraps non-npm package managers in GitLab CI", () => {
    const pnpmWorkflow = plan({
      ci: "gitlab-ci",
      package_manager: "pnpm",
      package_manager_version: "11.24.0",
    }).files.get(".gitlab-ci.yml");
    const bunWorkflow = plan({
      ci: "gitlab-ci",
      package_manager: "bun",
      package_manager_version: "1.3.14",
    }).files.get(".gitlab-ci.yml");

    expect(pnpmWorkflow).toContain("corepack enable");
    expect(pnpmWorkflow).toContain("corepack install --global pnpm@11.24.0");
    expect(bunWorkflow).toContain("image: oven/bun:1.3.14");
  });

  test("quotes CI commands as YAML data", () => {
    const command = 'node -e "console.log(\'key: value\')"\nprintf done';
    const workflow = plan({ ci: "github-actions", ci_commands: [command] })
      .files.get(".github/workflows/ci.yml");
    const parsed = parse(workflow!);

    expect(parsed.jobs.test.steps.at(-1)).toEqual({ run: command });
  });

  test("adds a dedicated Gitleaks CI job", () => {
    const github = parse(plan({ ci: "github-actions", secret_scan: "gitleaks" })
      .files.get(".github/workflows/ci.yml")!);
    const gitlab = parse(plan({ ci: "gitlab-ci", secret_scan: "gitleaks" })
      .files.get(".gitlab-ci.yml")!);

    expect(github.jobs.secrets.steps).toEqual(expect.arrayContaining([
      { uses: "gitleaks/gitleaks-action@v2" },
    ]));
    expect(gitlab.secrets.image).toMatch(/^zricethezav\/gitleaks:v\d/);
  });

  test("Lefthook includes only configured checks", () => {
    const lintOnly = plan({ hooks: "lefthook", quality: "biome", tests: "none" });
    expect(lintOnly.files.get("lefthook.yml")).toContain("lint:");
    expect(lintOnly.files.get("lefthook.yml")).not.toContain("test:");

    expect(() => plan({ hooks: "lefthook", quality: "none", tests: "none" }))
      .toThrow(/Lefthook requires/);
  });

  test("rejects CommonJS profiles with ESM-only entry templates", () => {
    expect(() => plan({ preset: "cli", http: "none", module: "commonjs" }))
      .toThrow(/CLI.*ESM/);
    expect(() => plan({ http: "fastify", module: "commonjs" }))
      .toThrow(/Fastify.*ESM/);
    expect(() => plan({ http: "nestjs", module: "commonjs" }))
      .toThrow(/NestJS.*ESM/);
  });
});
