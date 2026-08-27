import { readFileSync } from "node:fs";
import { valid, validRange } from "semver";
import { parse } from "yaml";
import { z } from "zod";

const exactVersionSchema = z.string().refine(
  (version) => valid(version) !== null,
  "Use an exact semantic version",
);
const versionRangeSchema = z.string().refine(
  (version) => validRange(version) !== null,
  "Use a valid semantic version or range",
);
const versionMapSchema = z.record(z.string(), versionRangeSchema);
const actionReferenceSchema = z.string().regex(
  /^[^/@\s]+\/[^@\s]+@[^@\s]+$/,
  "Use an owner/repository@ref action reference",
);
const taggedImageReferenceSchema = z.string().regex(
  /^[a-z0-9][a-z0-9._/-]*:[a-z0-9][a-z0-9._-]*$/i,
  "Use a tagged container image reference",
);
const imageRepositorySchema = z.string().regex(
  /^[a-z0-9][a-z0-9._/-]*$/i,
  "Use an untagged container image repository",
);

const scaffoldDefaultsSchema = z.object({
  schema_version: z.literal(1),
  generated_package_version: exactVersionSchema,
  runtime: z.object({
    node_version: z.string().regex(/^\d+(?:\.\d+){0,2}$/, "Use a Node.js version"),
    typescript_target: z.enum([
      "ES2015",
      "ES2016",
      "ES2017",
      "ES2018",
      "ES2019",
      "ES2020",
      "ES2021",
      "ES2022",
      "ES2023",
      "ES2024",
      "ESNext",
    ]),
  }).strict(),
  package_managers: z.object({
    pnpm: exactVersionSchema,
    npm: exactVersionSchema,
    yarn: exactVersionSchema,
    bun: exactVersionSchema,
  }).strict(),
  packages: versionMapSchema,
  provider_package_overrides: z.record(z.string(), versionMapSchema).default({}),
  framework_generators: z.object({
    "create-vite": exactVersionSchema,
  }).strict(),
  ci: z.object({
    runner: z.string().regex(/^[a-z0-9][a-z0-9._-]*$/i, "Use a runner label"),
    actions: z.object({
      checkout: actionReferenceSchema,
      setup_node: actionReferenceSchema,
      setup_bun: actionReferenceSchema,
      setup_pnpm: actionReferenceSchema,
      gitleaks: actionReferenceSchema,
    }).strict(),
    images: z.object({
      node: imageRepositorySchema,
      bun: imageRepositorySchema,
      gitleaks: taggedImageReferenceSchema,
    }).strict(),
  }).strict(),
}).strict();

export type ScaffoldDefaults = z.infer<typeof scaffoldDefaultsSchema>;

export function loadScaffoldDefaults(text: string): ScaffoldDefaults {
  let parsed: unknown;
  try {
    parsed = parse(text);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`Invalid scaffold defaults YAML: ${message}`);
  }

  const result = scaffoldDefaultsSchema.safeParse(parsed);
  if (!result.success) {
    const details = result.error.issues
      .map((issue) => `${issue.path.join(".") || "defaults"}: ${issue.message}`)
      .join("; ");
    throw new Error(`Invalid TypeScript scaffold defaults: ${details}`);
  }
  return result.data;
}

export const scaffoldDefaults = loadScaffoldDefaults(
  readFileSync(new URL("../config/defaults.yaml", import.meta.url), "utf8"),
);

export function defaultPackageVersion(packageName: string, providerId?: string): string {
  const providerVersion = providerId === undefined
    ? undefined
    : scaffoldDefaults.provider_package_overrides[providerId]?.[packageName];
  const version = providerVersion ?? scaffoldDefaults.packages[packageName];
  if (version === undefined) {
    throw new Error(`Missing default version for package ${packageName}`);
  }
  return version;
}

export function defaultPackageVersions(
  packageNames: readonly string[],
  providerId?: string,
): Record<string, string> {
  return Object.fromEntries(
    packageNames.map((packageName) => [
      packageName,
      defaultPackageVersion(packageName, providerId),
    ]),
  );
}
