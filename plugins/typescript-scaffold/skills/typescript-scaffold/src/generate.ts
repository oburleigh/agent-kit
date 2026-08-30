import { chmod, mkdir, rename, rm, stat, writeFile } from "node:fs/promises";
import { basename, dirname, join, resolve } from "node:path";
import { randomUUID } from "node:crypto";
import { execa } from "execa";
import { mergeFrameworkOutput, runOfficialFrameworkGenerator } from "./framework-generators.js";
import { createGenerationPlan, resolveProjectInput } from "./planning.js";
import { renderPlan } from "./render.js";
import type { ScaffoldProfile } from "./schema.js";
import { assertTargetAvailable } from "./target.js";

export type CommandRunner = (
  command: string,
  args: string[],
  options: { cwd: string },
) => Promise<void>;

export interface GenerationOptions {
  runCommand?: CommandRunner;
  readPackageManagerVersion?: (packageManager: string, cwd: string) => Promise<string>;
}

type HandledSignal = "SIGINT" | "SIGTERM";

export interface SignalRuntime {
  once(signal: HandledSignal, listener: () => void): void;
  off(signal: HandledSignal, listener: () => void): void;
  terminate(signal: HandledSignal): void;
}

export async function generateRepository(
  profile: ScaffoldProfile,
  target: string,
  options: GenerationOptions = {},
): Promise<void> {
  const absoluteTarget = resolve(target);
  await assertTargetAvailable(absoluteTarget);
  await assertParentDirectory(dirname(absoluteTarget));
  const workTarget = join(
    dirname(absoluteTarget),
    `.${basename(absoluteTarget)}.agent-kit-${randomUUID()}`,
  );
  const runCommand = options.runCommand ?? runExternalCommand;
  const project = resolveProjectInput(profile, absoluteTarget);
  const plan = createGenerationPlan(profile, project);

  await mkdir(workTarget, { recursive: false });
  const unregisterSignalCleanup = registerSignalCleanup(workTarget);
  try {
    const readVersion = options.readPackageManagerVersion
      ?? (options.runCommand
        ? async () => profile.package_manager_version
        : readInstalledPackageManagerVersion);
    let packageManagerVerified = false;
    if (profile.framework !== "none") {
      await verifyFrameworkPackageManager(profile, workTarget, readVersion);
      packageManagerVerified = true;
    }
    await runOfficialFrameworkGenerator(profile, workTarget, runCommand);
    await mergeFrameworkOutput(plan, workTarget);
    await renderPlan(plan, workTarget);
    await makeExecutables(workTarget, profile, plan.files);
    if (needsPackageManager(profile) && !packageManagerVerified) {
      await assertPackageManagerVersion(
        profile.package_manager,
        profile.package_manager_version,
        workTarget,
        readVersion,
      );
    }

    if (profile.install_dependencies) {
      const [command, ...args] = installCommand(profile.package_manager);
      await runCommand(command!, args, { cwd: workTarget });
      if (plan.packageJson.scripts.format) {
        const [formatCommand, ...formatArgs] = commandParts(
          `${packageRunCommand(profile.package_manager)} format`,
        );
        await runCommand(formatCommand!, formatArgs, { cwd: workTarget });
      }
    }
    if (profile.run_quality_gates) {
      for (const gate of plan.gates) {
        const [command, ...args] = commandParts(gate);
        await runCommand(command!, args, { cwd: workTarget });
      }
    }
    if (profile.initialize_git) {
      await runCommand("git", ["init", "--initial-branch=main"], { cwd: workTarget });
      const hookCommand = activateHooks(profile);
      if (hookCommand) {
        const [command, ...args] = hookCommand;
        await runCommand(command!, args, { cwd: workTarget });
      }
    }

    await rename(workTarget, absoluteTarget);
  } catch (error) {
    await rm(workTarget, { recursive: true, force: true });
    throw error;
  } finally {
    unregisterSignalCleanup();
  }
}

async function assertParentDirectory(parent: string): Promise<void> {
  try {
    const metadata = await stat(parent);
    if (!metadata.isDirectory()) throw new Error(`Parent path ${parent} is not a directory`);
  } catch (error) {
    if (isMissingPath(error)) throw new Error(`Parent directory ${parent} does not exist`);
    throw error;
  }
}

function isMissingPath(error: unknown): error is NodeJS.ErrnoException {
  return error instanceof Error && "code" in error && error.code === "ENOENT";
}

async function verifyFrameworkPackageManager(
  profile: ScaffoldProfile,
  target: string,
  readVersion: (packageManager: string, cwd: string) => Promise<string>,
): Promise<void> {
  const manifest = join(target, "package.json");
  await writeFile(
    manifest,
    `${JSON.stringify({
      name: "agent-kit-framework-staging",
      private: true,
      packageManager: `${profile.package_manager}@${profile.package_manager_version}`,
    })}\n`,
    { flag: "wx" },
  );
  try {
    await assertPackageManagerVersion(
      profile.package_manager,
      profile.package_manager_version,
      target,
      readVersion,
    );
  } finally {
    await rm(manifest, { force: true });
  }
}

export async function assertPackageManagerVersion(
  packageManager: string,
  expectedVersion: string,
  cwd = process.cwd(),
  readVersion: (packageManager: string, cwd: string) => Promise<string> = readInstalledPackageManagerVersion,
): Promise<void> {
  const actualVersion = (await readVersion(packageManager, cwd)).trim().replace(/^v/, "");
  if (actualVersion !== expectedVersion) {
    throw new Error(
      `Expected ${packageManager} ${expectedVersion}, but found ${actualVersion}. Install the selected version or update package_manager_version.`,
    );
  }
}

async function readInstalledPackageManagerVersion(
  packageManager: string,
  cwd: string,
): Promise<string> {
  try {
    const result = await execa(packageManager, ["--version"], { cwd });
    return result.stdout;
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`Cannot run ${packageManager} --version: ${message}`);
  }
}

function needsPackageManager(profile: ScaffoldProfile): boolean {
  return profile.install_dependencies
    || profile.run_quality_gates
    || (profile.initialize_git && profile.hooks !== "none")
    || profile.framework !== "none";
}

export function registerSignalCleanup(
  target: string,
  runtime: SignalRuntime = processSignalRuntime,
): () => void {
  let active = true;
  const listeners = new Map<HandledSignal, () => void>();
  const unregister = () => {
    if (!active) return;
    active = false;
    for (const [signal, listener] of listeners) runtime.off(signal, listener);
  };
  for (const signal of ["SIGINT", "SIGTERM"] as const) {
    const listener = () => {
      unregister();
      void rm(target, { recursive: true, force: true })
        .finally(() => runtime.terminate(signal));
    };
    listeners.set(signal, listener);
    runtime.once(signal, listener);
  }
  return unregister;
}

const processSignalRuntime: SignalRuntime = {
  once(signal, listener) {
    process.once(signal, listener);
  },
  off(signal, listener) {
    process.off(signal, listener);
  },
  terminate(signal) {
    process.kill(process.pid, signal);
  },
};

async function runExternalCommand(
  command: string,
  args: string[],
  options: { cwd: string },
): Promise<void> {
  await execa(command, args, { cwd: options.cwd, stdio: "inherit" });
}

function installCommand(packageManager: ScaffoldProfile["package_manager"]): string[] {
  if (packageManager === "npm") return ["npm", "install", "--ignore-scripts"];
  if (packageManager === "pnpm") return ["pnpm", "install", "--ignore-scripts"];
  if (packageManager === "yarn") return ["yarn", "install", "--mode=skip-build"];
  return ["bun", "install", "--ignore-scripts"];
}

function activateHooks(profile: ScaffoldProfile): string[] | undefined {
  if (profile.hooks === "none") return undefined;
  const executable = profile.package_manager === "bun"
    ? "bunx"
    : profile.package_manager;
  const execArgument = profile.package_manager === "npm" || profile.package_manager === "pnpm"
    ? ["exec"]
    : [];
  if (profile.hooks === "lefthook") {
    return [executable, ...execArgument, "lefthook", "install"];
  }
  return [executable, ...execArgument, "husky"];
}

function commandParts(command: string): string[] {
  return command.trim().split(/\s+/);
}

function packageRunCommand(packageManager: ScaffoldProfile["package_manager"]): string {
  if (packageManager === "npm") return "npm run";
  if (packageManager === "bun") return "bun run";
  return packageManager;
}

async function makeExecutables(
  target: string,
  profile: ScaffoldProfile,
  files: ReadonlyMap<string, string>,
): Promise<void> {
  if (profile.preset === "cli") await chmod(join(target, "src/cli.ts"), 0o755);
  if (profile.hooks === "husky-lint-staged") {
    await chmod(join(target, ".husky/pre-commit"), 0o755);
    if (profile.commit_lint === "commitlint") {
      await chmod(join(target, ".husky/commit-msg"), 0o755);
    }
    if (files.has(".husky/pre-push")) {
      await chmod(join(target, ".husky/pre-push"), 0o755);
    }
  }
}
