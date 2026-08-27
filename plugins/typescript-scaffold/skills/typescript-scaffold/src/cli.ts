import { access, readFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { parseArgs } from "node:util";
import { generateRepository } from "./generate.js";
import { loadProfileText } from "./profile.js";
import {
  createProfileFromPreset,
  resolveProfileDirectory,
  type PresetName,
} from "./profiles.js";

export async function main(args: string[]): Promise<string> {
  const { values } = parseArgs({
    args,
    allowPositionals: false,
    strict: true,
    options: {
      profile: { type: "string" },
      target: { type: "string" },
    },
  });
  if (!values.profile || !values.target) {
    throw new Error("--profile and --target are required");
  }

  const profilePath = await resolveProfileArgument(values.profile);
  const target = resolve(values.target);
  const profile = loadProfileText(await readFile(profilePath, "utf8"));
  await generateRepository(profile, target);
  return target;
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
  main(process.argv.slice(2))
    .then((target) => console.log(`Created ${target}`))
    .catch((error: unknown) => {
      console.error(error instanceof Error ? error.message : String(error));
      process.exitCode = 1;
    });
}
