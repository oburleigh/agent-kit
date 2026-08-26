import { z } from "zod";
import { valid as validSemver } from "semver";

const dependencyListSchema = z.array(
  z.object({
    name: z.string().min(1),
    version: z.string().min(1).default("latest"),
  }).strict(),
);

export const profileSchema = z.object({
  schema_version: z.literal(1),
  name: z.string().min(1),
  preset: z.enum(["library", "service", "cli", "workspace"]),
  package_manager: z.enum(["pnpm", "npm", "yarn", "bun"]),
  package_manager_version: z.string().refine(
    (version) => validSemver(version) !== null,
    "Use an exact semantic version for package_manager_version",
  ),
  module: z.enum(["esm", "commonjs"]),
  build: z.enum(["tsc", "tsup", "framework-owned"]),
  quality: z.enum(["biome", "eslint-prettier", "none"]),
  tests: z.enum(["vitest", "node-test", "jest", "none"]),
  runtime_validation: z.enum(["zod", "valibot", "none"]),
  http: z.enum(["fastify", "express", "hono", "nestjs", "none"]),
  logging: z.enum(["pino", "winston", "none"]),
  hooks: z.enum(["lefthook", "husky-lint-staged", "none"]),
  ci: z.enum(["github-actions", "gitlab-ci", "none"]),
  publishing: z.enum(["npm", "none"]),
  workspace: z.enum(["none", "turbo", "nx"]),
  secret_scan: z.enum(["gitleaks", "none"]),
  duplication: z.enum(["jscpd", "none"]),
  framework: z.enum(["none", "vite-react"]),
  license: z.enum(["apache-2.0", "mit", "none"]),
  install_dependencies: z.boolean(),
  run_quality_gates: z.boolean(),
  initialize_git: z.boolean(),
  default_author: z.string(),
  project: z.object({
    name: z.string(),
    description: z.string(),
    author: z.string(),
    repository_url: z.string(),
  }).strict().default({
    name: "",
    description: "",
    author: "",
    repository_url: "",
  }),
  package_versions: z.record(z.string(), z.string().min(1)),
  extra_dependencies: dependencyListSchema,
  extra_dev_dependencies: dependencyListSchema,
  extra_scripts: z.record(z.string(), z.string()),
  ci_commands: z.array(z.string().min(1)),
}).strict();

export type ScaffoldProfile = z.infer<typeof profileSchema>;
