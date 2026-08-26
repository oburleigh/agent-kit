import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import envPaths from "env-paths";
import { stringify } from "yaml";
import { loadProfileText } from "./profile.js";
import type { ScaffoldProfile } from "./schema.js";

export type PresetName = ScaffoldProfile["preset"];

export function resolveProfileDirectory(
  environment: NodeJS.ProcessEnv = process.env,
): string {
  const root = environment.AGENT_KIT_CONFIG_DIR
    ?? envPaths("agent-kit", { suffix: "" }).config;
  return join(root, "scaffolds", "typescript");
}

export async function loadBundledPreset(name: PresetName): Promise<ScaffoldProfile> {
  const path = fileURLToPath(new URL(`../config/presets/${name}.yaml`, import.meta.url));
  return loadProfileText(await readFile(path, "utf8"));
}

export async function createProfileFromPreset(
  presetName: PresetName,
  profileName: string,
  directory = resolveProfileDirectory(),
): Promise<string> {
  if (!/^[a-z0-9][a-z0-9._-]*$/i.test(profileName)) {
    throw new Error("Profile names may contain letters, numbers, dots, underscores, and hyphens");
  }

  const preset = await loadBundledPreset(presetName);
  const path = join(directory, `${profileName}.yaml`);
  await mkdir(directory, { recursive: true });
  try {
    await writeFile(path, stringify({ ...preset, name: profileName }), {
      encoding: "utf8",
      flag: "wx",
    });
  } catch (error) {
    if (isExistingPath(error)) {
      throw new Error(`Profile already exists: ${path}`);
    }
    throw error;
  }
  return path;
}

function isExistingPath(error: unknown): error is NodeJS.ErrnoException {
  return error instanceof Error && "code" in error && error.code === "EEXIST";
}
