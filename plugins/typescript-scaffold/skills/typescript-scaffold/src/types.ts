import type { ScaffoldProfile } from "./schema.js";

export interface ProjectInput {
  name: string;
  description: string;
  author: string;
  repositoryUrl?: string;
}

export interface PackageJsonPlan {
  name: string;
  version: string;
  description: string;
  private: boolean;
  type: "module" | "commonjs";
  packageManager: string;
  license?: string;
  author?: string;
  repository?: { type: "git"; url: string };
  scripts: Record<string, string>;
  dependencies: Record<string, string>;
  devDependencies: Record<string, string>;
  [key: string]: unknown;
}

export interface GenerationPlan {
  profile: ScaffoldProfile;
  project: ProjectInput;
  packageJson: PackageJsonPlan;
  files: Map<string, string>;
  gates: string[];
}

export interface ProviderContext {
  profile: ScaffoldProfile;
  project: ProjectInput;
  packageCommand: string;
  packageRun: string;
  scripts: Readonly<Record<string, string>>;
  versionFor(packageName: string, fallback: string): string;
}

export interface ProviderContribution {
  id: string;
  selected(profile: ScaffoldProfile): boolean;
  validate?(context: ProviderContext): void;
  dependencies?: Record<string, string>;
  devDependencies?: Record<string, string>;
  scripts?: Record<string, string> | ((context: ProviderContext) => Record<string, string>);
  packageJson?: Record<string, unknown> | ((context: ProviderContext) => Record<string, unknown>);
  ignore?: string[];
  files?(context: ProviderContext): Record<string, string>;
}
