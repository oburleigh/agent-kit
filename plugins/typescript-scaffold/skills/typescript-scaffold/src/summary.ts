import { resolve } from "node:path";
import { createGenerationPlan, resolveProjectInput } from "./planning.js";
import type { ScaffoldProfile } from "./schema.js";

const providerFields = [
  "build",
  "ci",
  "commit_lint",
  "duplication",
  "framework",
  "hooks",
  "http",
  "license",
  "logging",
  "publishing",
  "quality",
  "runtime_validation",
  "secret_scan",
  "tests",
  "workspace",
] as const;

export function createPlanSummary(profile: ScaffoldProfile, target: string) {
  const absoluteTarget = resolve(target);
  const project = resolveProjectInput(profile, absoluteTarget);
  const plan = createGenerationPlan(profile, project);
  const selectedProviders: Record<string, string> = {
    module: profile.module,
    package_manager: `${profile.package_manager}@${profile.package_manager_version}`,
  };
  const disabledProviders: string[] = [];
  for (const field of providerFields) {
    const value = profile[field] ?? "none";
    if (value === "none") disabledProviders.push(field);
    else selectedProviders[field] = value;
  }

  return {
    schema_version: 1,
    target: absoluteTarget,
    preset: profile.preset,
    project: {
      name: project.name,
      description: project.description,
      author: project.author,
      repository_url: project.repositoryUrl ?? "",
    },
    selected_providers: selectedProviders,
    disabled_providers: disabledProviders,
    workspace_members: profile.workspace_members ?? [],
    quality_gates: plan.gates,
    execution: {
      install_dependencies: profile.install_dependencies,
      run_quality_gates: profile.run_quality_gates,
      initialize_git: profile.initialize_git,
    },
  };
}
