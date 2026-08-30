import { access, readFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { parseArgs } from "node:util";
import { generateRepository } from "./generate.js";
import { loadProfileText } from "./profile.js";
import {
  assertValidProfileName,
  createProfileFromPreset,
  loadBundledPreset,
  resolveProfileDirectory,
  type PresetName,
} from "./profiles.js";
import type { ScaffoldProfile } from "./schema.js";
import { createPlanSummary } from "./summary.js";

type CliResult =
  | { mode: "generate"; target: string }
  | { mode: "plan"; summary: ReturnType<typeof createPlanSummary> };

type ProfileSelection =
  | { path: string }
  | {
    path: string;
    missing: { preset: PresetName; profileName: string; directory: string };
  };

export async function main(
  args: string[],
  environment: NodeJS.ProcessEnv = process.env,
): Promise<string> {
  const result = await executeCli(args, environment);
  return result.mode === "plan" ? JSON.stringify(result.summary) : result.target;
}

async function executeCli(
  args: string[],
  environment: NodeJS.ProcessEnv = process.env,
): Promise<CliResult> {
  const { values } = parseArgs({
    args,
    allowPositionals: false,
    strict: true,
    options: {
      profile: { type: "string" },
      target: { type: "string" },
      plan: { type: "boolean", default: false },
    },
  });
  if (!values.profile || !values.target) {
    throw new Error("--profile and --target are required");
  }

  if (values.plan) {
    const profile = await loadProfileForPlan(values.profile, environment);
    return { mode: "plan", summary: createPlanSummary(profile, values.target) };
  }

  const profilePath = await resolveProfileArgument(values.profile, environment);
  const target = resolve(values.target);
  const profile = loadProfileText(await readFile(profilePath, "utf8"));
  await generateRepository(profile, target);
  return { mode: "generate", target };
}

async function loadProfileForPlan(
  value: string,
  environment: NodeJS.ProcessEnv,
): Promise<ScaffoldProfile> {
  const selection = await selectProfileArgument(value, environment);
  if (!("missing" in selection)) {
    return loadProfileText(await readFile(selection.path, "utf8"));
  }
  return {
    ...await loadBundledPreset(selection.missing.preset),
    name: selection.missing.profileName,
  };
}

export async function resolveProfileArgument(
  value: string,
  environment: NodeJS.ProcessEnv = process.env,
): Promise<string> {
  const selection = await selectProfileArgument(value, environment);
  if (!("missing" in selection)) return selection.path;
  return createProfileFromPreset(
    selection.missing.preset,
    selection.missing.profileName,
    selection.missing.directory,
  );
}

async function selectProfileArgument(
  value: string,
  environment: NodeJS.ProcessEnv,
): Promise<ProfileSelection> {
  if (looksLikePath(value)) return { path: resolve(value) };

  const [presetCandidate, profileCandidate, ...extra] = value.split(":");
  if (extra.length > 0 || !presetCandidate) {
    throw new Error(`Invalid profile selector: ${value}`);
  }
  const directory = resolveProfileDirectory(environment);
  const profileName = profileCandidate || presetCandidate;
  const profilePath = join(directory, `${profileName}.yaml`);
  try {
    await access(profilePath);
    return { path: profilePath };
  } catch (error) {
    if (!isMissingPath(error)) throw error;
  }

  if (!isPresetName(presetCandidate)) {
    throw new Error(`Profile does not exist: ${profilePath}. Use <preset>:<profile-name> to create it.`);
  }
  assertValidProfileName(profileName);
  return {
    path: profilePath,
    missing: { preset: presetCandidate, profileName, directory },
  };
}

function looksLikePath(value: string): boolean {
  return value.includes("/")
    || value.includes("\\")
    || value.endsWith(".yaml")
    || value.endsWith(".yml")
    || value.startsWith(".");
}

function isPresetName(value: string): value is PresetName {
  return ["library", "service", "cli", "workspace"].includes(value);
}

function isMissingPath(error: unknown): error is NodeJS.ErrnoException {
  return error instanceof Error && "code" in error && error.code === "ENOENT";
}

const executablePath = process.argv[1] ? pathToFileURL(resolve(process.argv[1])).href : "";
if (import.meta.url === executablePath) {
  const args = process.argv.slice(2);
  executeCli(args)
    .then((result) => {
      console.log(result.mode === "plan"
        ? JSON.stringify(result.summary)
        : `Created ${result.target}`);
    })
    .catch((error: unknown) => {
      console.error(error instanceof Error ? error.message : String(error));
      process.exitCode = 1;
    });
}
