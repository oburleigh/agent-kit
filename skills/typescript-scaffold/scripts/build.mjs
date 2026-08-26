import { chmod, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";
import { build } from "esbuild";

await mkdir("dist", { recursive: true });
await mkdir("config", { recursive: true });

await build({
  entryPoints: ["src/cli.ts"],
  outfile: "dist/generate.mjs",
  bundle: true,
  platform: "node",
  format: "esm",
  target: "node24",
  banner: {
    js: "#!/usr/bin/env node\nimport { createRequire as __agentKitCreateRequire } from \"node:module\";\nconst require = __agentKitCreateRequire(import.meta.url);",
  },
  legalComments: "none",
});
const bundledGenerator = await readFile("dist/generate.mjs", "utf8");
await writeFile("dist/generate.mjs", bundledGenerator.replace(/[ \t]+$/gm, ""));
await chmod("dist/generate.mjs", 0o755);

const schemaBundle = "dist/.write-schema.mjs";
await build({
  entryPoints: ["scripts/schema-entry.ts"],
  outfile: schemaBundle,
  bundle: true,
  platform: "node",
  format: "esm",
  target: "node24",
  legalComments: "none",
});
try {
  await import(`${pathToFileURL(schemaBundle).href}?build=${Date.now()}`);
} finally {
  await rm(schemaBundle, { force: true });
}
