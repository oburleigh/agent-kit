import { providerCatalog } from "../providers/catalog.js";
import validatePackageName from "validate-npm-package-name";
import type { ScaffoldProfile } from "./schema.js";
import type {
  GenerationPlan,
  PackageJsonPlan,
  ProjectInput,
  ProviderContext,
  ProviderContribution,
} from "./types.js";

const packageManagerCommands = {
  pnpm: { command: "pnpm", run: "pnpm" },
  npm: { command: "npm", run: "npm run" },
  yarn: { command: "yarn", run: "yarn" },
  bun: { command: "bun", run: "bun run" },
} as const;

export function createGenerationPlan(
  profile: ScaffoldProfile,
  project: ProjectInput,
): GenerationPlan {
  const packageNameResult = validatePackageName(project.name);
  if (!packageNameResult.validForNewPackages) {
    const reasons = [
      ...(packageNameResult.errors ?? []),
      ...(packageNameResult.warnings ?? []),
    ].join("; ");
    throw new Error(`Invalid package name ${project.name}: ${reasons}`);
  }
  if (profile.license === "mit" && project.author.trim() === "") {
    throw new Error("The MIT licence requires an author");
  }
  const context = createProviderContext(profile, project, {});

  validateGlobalCompatibility(profile);
  const selected = providerCatalog.filter((provider) => provider.selected(profile));
  for (const provider of selected) provider.validate?.(context);

  const packageJson: PackageJsonPlan = {
    name: project.name,
    version: "0.1.0",
    description: project.description,
    private: profile.publishing === "none",
    type: profile.module === "esm" ? "module" : "commonjs",
    packageManager: `${profile.package_manager}@${profile.package_manager_version}`,
    engines: { node: ">=24" },
    ...(profile.license === "none" ? {} : {
      license: profile.license === "apache-2.0" ? "Apache-2.0" : "MIT",
    }),
    ...(project.author ? { author: project.author } : {}),
    ...(project.repositoryUrl ? {
      repository: { type: "git" as const, url: project.repositoryUrl },
    } : {}),
    scripts: {},
    dependencies: {},
    devDependencies: {},
  };
  let files = new Map<string, string>();

  for (const provider of selected) {
    mergePackageJson(packageJson, provider.packageJson, provider.id);
    mergeStringRecord(
      packageJson.scripts,
      typeof provider.scripts === "function" ? provider.scripts(context) : provider.scripts,
      "script",
      provider.id,
    );
    mergeDependencies(packageJson.dependencies, provider.dependencies, context, provider.id);
    mergeDependencies(packageJson.devDependencies, provider.devDependencies, context, provider.id);
  }

  mergeDependencies(
    packageJson.dependencies,
    Object.fromEntries(profile.extra_dependencies.map(({ name, version }) => [name, version])),
    context,
    "profile extra_dependencies",
    false,
  );
  mergeDependencies(
    packageJson.devDependencies,
    Object.fromEntries(profile.extra_dev_dependencies.map(({ name, version }) => [name, version])),
    context,
    "profile extra_dev_dependencies",
    false,
  );
  mergeStringRecord(packageJson.scripts, profile.extra_scripts, "script", "profile extra_scripts");
  rejectDependencyBucketConflicts(packageJson);
  context.scripts = packageJson.scripts;
  files = collectProviderFiles(selected, context);

  const gates = gatesForScripts(profile, packageJson.scripts);

  return { profile, project, packageJson, files, gates };
}

export function refreshPlanFiles(plan: GenerationPlan): void {
  const selected = providerCatalog.filter((provider) => provider.selected(plan.profile));
  const context = createProviderContext(plan.profile, plan.project, plan.packageJson.scripts);
  plan.files = collectProviderFiles(selected, context);
}

function createProviderContext(
  profile: ScaffoldProfile,
  project: ProjectInput,
  scripts: Readonly<Record<string, string>>,
): ProviderContext {
  const commands = packageManagerCommands[profile.package_manager];
  return {
    profile,
    project,
    packageCommand: commands.command,
    packageRun: commands.run,
    scripts,
    versionFor(packageName, fallback) {
      return profile.package_versions[packageName] ?? fallback;
    },
  };
}

function collectProviderFiles(
  selected: readonly ProviderContribution[],
  context: ProviderContext,
): Map<string, string> {
  const files = new Map<string, string>();
  for (const provider of selected) {
    for (const [path, content] of Object.entries(provider.files?.(context) ?? {})) {
      const existing = files.get(path);
      if (existing !== undefined && existing !== content) {
        throw new Error(`Providers conflict on file ${path}: ${provider.id}`);
      }
      files.set(path, content);
    }
  }
  const ignore = [...new Set(selected.flatMap((provider) => provider.ignore ?? []))];
  files.set(".gitignore", `${ignore.join("\n")}\n`);
  return files;
}

export function gatesForScripts(
  profile: ScaffoldProfile,
  scripts: Readonly<Record<string, string>>,
): string[] {
  const run = packageManagerCommands[profile.package_manager].run;
  return ["lint", "typecheck", "test", "build", "duplication", "secrets"]
    .filter((script) => scripts[script] !== undefined)
    .map((script) => `${run} ${script}`);
}

export function rejectDependencyBucketConflicts(packageJson: PackageJsonPlan): void {
  for (const name of Object.keys(packageJson.dependencies)) {
    if (packageJson.devDependencies[name] !== undefined) {
      throw new Error(
        `Dependency ${name} cannot appear in both dependencies and devDependencies`,
      );
    }
  }
}

function validateGlobalCompatibility(profile: ScaffoldProfile): void {
  if (profile.run_quality_gates && !profile.install_dependencies) {
    throw new Error("Quality gates require dependency installation");
  }
  if (profile.http !== "none" && profile.preset !== "service") {
    throw new Error("HTTP providers require the service preset");
  }
  if (profile.workspace !== "none" && profile.preset !== "workspace") {
    throw new Error("Workspace providers require the workspace preset");
  }
  if (profile.preset === "workspace" && profile.workspace === "none") {
    throw new Error("The workspace preset requires Turbo or Nx");
  }
  if (profile.hooks === "husky-lint-staged" && profile.quality !== "eslint-prettier") {
    throw new Error("Husky with lint-staged requires the ESLint and Prettier provider");
  }
  if (profile.framework === "vite-react" && profile.preset !== "library") {
    throw new Error("The Vite React adapter requires the library preset");
  }
  if (profile.framework === "vite-react" && profile.publishing !== "none") {
    throw new Error("The Vite React adapter requires publishing disabled");
  }
  if (profile.framework === "vite-react" && profile.build !== "framework-owned") {
    throw new Error("The Vite React adapter requires framework-owned build");
  }
  if (profile.framework === "vite-react" && profile.module !== "esm") {
    throw new Error("The Vite React adapter requires ESM");
  }
  if (profile.framework === "vite-react" && profile.quality !== "none") {
    throw new Error("The Vite React adapter requires quality set to none because Vite owns linting");
  }
  if (profile.framework === "vite-react" && !["none", "vitest"].includes(profile.tests)) {
    throw new Error("The Vite React adapter supports Vitest or no test provider");
  }
  if (profile.http !== "fastify" && profile.runtime_validation !== "none") {
    throw new Error("Runtime validation integrations currently require Fastify");
  }
  if (profile.http !== "fastify" && profile.logging !== "none") {
    throw new Error("Logging integrations currently require Fastify");
  }
  if (profile.http === "nestjs" && profile.tests === "node-test") {
    throw new Error("NestJS requires Vitest or Jest because Node type stripping cannot transform decorators");
  }
  if (profile.http === "nestjs" && profile.build !== "tsc") {
    throw new Error("NestJS requires the tsc build provider to emit decorator metadata");
  }
  if (profile.module === "commonjs" && profile.preset === "cli") {
    throw new Error("The CLI preset requires ESM");
  }
  if (profile.module === "commonjs" && profile.http === "fastify") {
    throw new Error("The Fastify integration requires ESM");
  }
  if (profile.module === "commonjs" && profile.http === "nestjs") {
    throw new Error("The NestJS integration requires ESM");
  }
}

function mergePackageJson(
  target: PackageJsonPlan,
  contribution: Record<string, unknown> | undefined,
  providerId: string,
): void {
  if (!contribution) return;
  for (const [key, value] of Object.entries(contribution)) {
    const existing = target[key];
    if (existing !== undefined && !sameValue(existing, value) && !canOverridePackageField(key)) {
      throw new Error(`Providers conflict on package.json field ${key}: ${providerId}`);
    }
    target[key] = value;
  }
}

function canOverridePackageField(key: string): boolean {
  return key === "private" || key === "type";
}

function mergeStringRecord(
  target: Record<string, string>,
  contribution: Record<string, string> | undefined,
  kind: string,
  providerId: string,
): void {
  if (!contribution) return;
  for (const [name, value] of Object.entries(contribution)) {
    const existing = target[name];
    if (existing !== undefined && existing !== value) {
      throw new Error(`Providers conflict on ${kind} ${name}: ${providerId}`);
    }
    target[name] = value;
  }
}

function mergeDependencies(
  target: Record<string, string>,
  contribution: Record<string, string> | undefined,
  context: ProviderContext,
  providerId: string,
  resolveProfileVersion = true,
): void {
  if (!contribution) return;
  for (const [name, fallback] of Object.entries(contribution)) {
    const version = resolveProfileVersion ? context.versionFor(name, fallback) : fallback;
    const existing = target[name];
    if (existing !== undefined && existing !== version) {
      throw new Error(`Providers conflict on dependency ${name}: ${providerId}`);
    }
    target[name] = version;
  }
}

function sameValue(left: unknown, right: unknown): boolean {
  return JSON.stringify(left) === JSON.stringify(right);
}
