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

export async function main(
  args: string[],
  environment: NodeJS.ProcessEnv = process.env,
): Promise<string> {
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
    return JSON.stringify(createPlanSummary(profile, values.target));
  }

  const profilePath = await resolveProfileArgument(values.profile, environment);
  const target = resolve(values.target);
  const profile = loadProfileText(await readFile(profilePath, "utf8"));
  await generateRepository(profile, target);
  return target;
}

async function loadProfileForPlan(
  value: string,
  environment: NodeJS.ProcessEnv,
): Promise<ScaffoldProfile> {
  if (looksLikePath(value)) {
    return loadProfileText(await readFile(resolve(value), "utf8"));
  }

  const [presetCandidate, profileCandidate, ...extra] = value.split(":");
  if (extra.length > 0 || !presetCandidate) {
    throw new Error(`Invalid profile selector: ${value}`);
  }
  const profileName = profileCandidate || presetCandidate;
  assertValidProfileName(profileName);
  const profilePath = join(resolveProfileDirectory(environment), `${profileName}.yaml`);
  try {
    return loadProfileText(await readFile(profilePath, "utf8"));
  } catch (error) {
    if (!isMissingPath(error)) throw error;
  }
  if (!isPresetName(presetCandidate)) {
    throw new Error(`Profile does not exist: ${profilePath}. Use <preset>:<profile-name> to create it.`);
  }
  return { ...await loadBundledPreset(presetCandidate), name: profileName };
}

export async function resolveProfileArgument(
  value: string,
  environment: NodeJS.ProcessEnv = process.env,
): Promise<string> {
  if (looksLikePath(value)) return resolve(value);

  const [presetCandidate, profileCandidate, ...extra] = value.split(":");
  if (extra.length > 0 || !presetCandidate) {
    throw new Error(`Invalid profile selector: ${value}`);
  }
  const directory = resolveProfileDirectory(environment);
  const profileName = profileCandidate || presetCandidate;
  const profilePath = join(directory, `${profileName}.yaml`);
  try {
    await access(profilePath);
    return profilePath;
  } catch (error) {
    if (!isMissingPath(error)) throw error;
  }

  if (!isPresetName(presetCandidate)) {
    throw new Error(`Profile does not exist: ${profilePath}. Use <preset>:<profile-name> to create it.`);
  }
  return createProfileFromPreset(presetCandidate, profileName, directory);
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
  main(args)
    .then((result) => {
      console.log(args.includes("--plan") ? result : `Created ${result}`);
    })
    .catch((error: unknown) => {
      console.error(error instanceof Error ? error.message : String(error));
      process.exitCode = 1;
    });
}
