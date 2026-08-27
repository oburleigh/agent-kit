import { resolve, sep } from "node:path";
import stringify from "json-stringify-pretty-compact";
import nodePlop from "node-plop";
import type { GenerationPlan } from "./types.js";

export async function renderPlan(plan: GenerationPlan, target: string): Promise<void> {
  const files = new Map(plan.files);
  files.set("package.json", `${stringify(plan.packageJson)}\n`);
  for (const path of files.keys()) assertSafeRelativePath(target, path);

  const plop = await nodePlop(undefined, { destBasePath: target, force: false });
  const generator = plop.setGenerator("typescript-repository", {
    description: "Render a planned TypeScript repository",
    prompts: [],
    actions: [...files.entries()].map(([path, content]) => ({
      type: "add" as const,
      path,
      template: "{{{content}}}",
      data: { content },
      abortOnFail: true,
    })),
  });
  const result = await generator.runActions({});
  if (result.failures.length > 0) {
    const details = result.failures.map(({ path, error }) => `${path}: ${error}`).join("; ");
    throw new Error(`Repository rendering failed: ${details}`);
  }
}

export function assertSafeRelativePath(target: string, path: string): void {
  const root = resolve(target);
  const destination = resolve(root, path);
  if (destination !== root && !destination.startsWith(`${root}${sep}`)) {
    throw new Error(`Provider file escapes the target: ${path}`);
  }
}
