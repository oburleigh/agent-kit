import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import envPaths from "env-paths";
import { parse, stringify } from "yaml";
import { scaffoldDefaults } from "./defaults.js";
import { profileSchema, type ScaffoldProfile } from "./schema.js";

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
  return loadBundledPresetText(await readFile(path, "utf8"));
}

const presetTemplateSchema = profileSchema.omit({
  package_manager_version: true,
  package_versions: true,
});

export function loadBundledPresetText(input: string): ScaffoldProfile {
  let parsed: unknown;
  try {
    parsed = parse(input);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`Invalid bundled preset YAML: ${message}`);
  }
  const result = presetTemplateSchema.safeParse(parsed);
  if (!result.success) {
    const details = result.error.issues
      .map((issue) => `${issue.path.join(".") || "preset"}: ${issue.message}`)
      .join("; ");
    throw new Error(`Invalid TypeScript scaffold preset: ${details}`);
  }
  return profileSchema.parse({
    ...result.data,
    package_manager_version: scaffoldDefaults.package_managers[result.data.package_manager],
    package_versions: {},
  });
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
