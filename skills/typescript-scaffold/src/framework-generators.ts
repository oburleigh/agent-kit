import { readFile, rm } from "node:fs/promises";
import { join } from "node:path";
import { scaffoldDefaults } from "./defaults.js";
import type { ScaffoldProfile } from "./schema.js";
import type { CommandRunner } from "./generate.js";
import type { GenerationPlan, PackageJsonPlan } from "./types.js";
import { assertSafeRelativePath } from "./render.js";
import {
  gatesForScripts,
  refreshPlanFiles,
  rejectDependencyBucketConflicts,
} from "./planning.js";

export async function runOfficialFrameworkGenerator(
  profile: ScaffoldProfile,
  target: string,
  runCommand: CommandRunner,
): Promise<void> {
  if (profile.framework === "none") return;
  if (profile.framework === "vite-react") {
    const version = profile.package_versions["create-vite"]
      ?? scaffoldDefaults.framework_generators["create-vite"];
    const [command, args] = viteGeneratorCommand(profile.package_manager, version);
    await runCommand(command, args, { cwd: target });
  }
}

export function frameworkGateNames(profile: ScaffoldProfile): string[] {
  return profile.framework === "vite-react" ? ["lint", "build"] : [];
}

function viteGeneratorCommand(
  packageManager: ScaffoldProfile["package_manager"],
  version: string,
): [string, string[]] {
  if (packageManager === "pnpm") {
    return ["pnpm", ["create", `vite@${version}`, ".", "--template", "react-ts"]];
  }
  if (packageManager === "yarn") {
    return ["yarn", ["dlx", `create-vite@${version}`, ".", "--template", "react-ts"]];
  }
  if (packageManager === "bun") {
    return ["bun", ["create", `vite@${version}`, ".", "--template", "react-ts"]];
  }
  return ["npm", ["create", `vite@${version}`, ".", "--", "--template", "react-ts"]];
}

export async function mergeFrameworkOutput(
  plan: GenerationPlan,
  target: string,
): Promise<void> {
  if (plan.profile.framework === "none") return;
  for (const path of plan.files.keys()) assertSafeRelativePath(target, path);
  const packagePath = join(target, "package.json");
  const frameworkPackage = JSON.parse(await readFile(packagePath, "utf8")) as PackageJsonPlan;
  rejectFrameworkMapConflicts("script", frameworkPackage.scripts, plan.packageJson.scripts);
  rejectFrameworkMapConflicts(
    "dependency",
    frameworkPackage.dependencies,
    plan.packageJson.dependencies,
  );
  rejectFrameworkMapConflicts(
    "devDependency",
    frameworkPackage.devDependencies,
    plan.packageJson.devDependencies,
  );
  plan.packageJson = {
    ...frameworkPackage,
    ...plan.packageJson,
    scripts: { ...frameworkPackage.scripts, ...plan.packageJson.scripts },
    dependencies: { ...frameworkPackage.dependencies, ...plan.packageJson.dependencies },
    devDependencies: { ...frameworkPackage.devDependencies, ...plan.packageJson.devDependencies },
  };
  rejectDependencyBucketConflicts(plan.packageJson);
  plan.gates = gatesForScripts(plan.profile, plan.packageJson.scripts);
  refreshPlanFiles(plan);

  for (const path of plan.files.keys()) assertSafeRelativePath(target, path);
  await rm(packagePath);
  for (const path of plan.files.keys()) {
    await rm(join(target, path), { recursive: true, force: true });
  }
}

function rejectFrameworkMapConflicts(
  kind: string,
  frameworkValues: Record<string, string> | undefined,
  plannedValues: Record<string, string>,
): void {
  for (const [name, planned] of Object.entries(plannedValues)) {
    const official = frameworkValues?.[name];
    if (official !== undefined && official !== planned) {
      throw new Error(
        `Framework generator conflicts on ${kind} ${name}: official ${official}, profile ${planned}`,
      );
    }
  }
}
