import type { ProviderContext } from "../src/types.js";
import stringify from "json-stringify-pretty-compact";

export function packageVersions(
  context: ProviderContext,
  packages: Record<string, string>,
): Record<string, string> {
  return Object.fromEntries(
    Object.entries(packages).map(([name, fallback]) => [
      name,
      context.versionFor(name, fallback),
    ]),
  );
}

export function json(value: unknown): string {
  return `${stringify(value)}\n`;
}
