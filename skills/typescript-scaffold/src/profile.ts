import { parse } from "yaml";
import { profileSchema, type ScaffoldProfile } from "./schema.js";

export function loadProfileText(input: string): ScaffoldProfile {
  let parsed: unknown;
  try {
    parsed = parse(input);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`Invalid profile YAML: ${message}`);
  }

  const result = profileSchema.safeParse(parsed);
  if (!result.success) {
    const details = result.error.issues
      .map((issue) => `${issue.path.join(".") || "profile"}: ${issue.message}`)
      .join("; ");
    throw new Error(`Invalid TypeScript scaffold profile: ${details}`);
  }

  return {
    ...result.data,
    commit_lint: result.data.commit_lint ?? "none",
    workspace_members: result.data.workspace_members ?? [],
  };
}
