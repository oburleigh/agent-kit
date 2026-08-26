import { defaultPackageVersions } from "../src/defaults.js";
import type { ProviderContribution } from "../src/types.js";

function requireService(preset: string): void {
  if (preset !== "service") {
    throw new Error("HTTP providers require the service preset");
  }
}

export const httpProviders: ProviderContribution[] = [
  {
    id: "http-fastify",
    selected: (profile) => profile.http === "fastify",
    validate: ({ profile }) => requireService(profile.preset),
    dependencies: defaultPackageVersions(["fastify"], "http-fastify"),
    files: (context) => fastifyFiles(context),
  },
  {
    id: "http-express",
    selected: (profile) => profile.http === "express",
    validate: ({ profile }) => requireService(profile.preset),
    dependencies: defaultPackageVersions(["express"], "http-express"),
    devDependencies: defaultPackageVersions(["@types/express"], "http-express"),
    files: (context) => withTest({
      "src/app.ts": "import express from \"express\";\n\nexport function buildApp() {\n  const app = express();\n  app.use(express.json());\n  app.get(\"/health\", (_request, response) => {\n    void _request;\n    return response.json({ status: \"ok\" });\n  });\n  return app;\n}\n",
      "src/server.ts": "import { buildApp } from \"./app.js\";\n\nconst port = Number(process.env.PORT ?? 3000);\nbuildApp().listen(port, () => console.log(`Listening on ${port}`));\n",
    }, expressTest(context.profile.tests)),
  },
  {
    id: "http-hono",
    selected: (profile) => profile.http === "hono",
    validate: ({ profile }) => requireService(profile.preset),
    dependencies: defaultPackageVersions(["hono", "@hono/node-server"], "http-hono"),
    files: (context) => withTest({
      "src/app.ts": "import { Hono } from \"hono\";\n\nexport const app = new Hono();\napp.get(\"/health\", (context) => context.json({ status: \"ok\" }));\n",
      "src/server.ts": "import { serve } from \"@hono/node-server\";\nimport { app } from \"./app.js\";\n\nserve({ fetch: app.fetch, port: Number(process.env.PORT ?? 3000) });\n",
    }, honoTest(context.profile.tests)),
  },
  {
    id: "http-nestjs",
    selected: (profile) => profile.http === "nestjs",
    validate: ({ profile }) => requireService(profile.preset),
    dependencies: defaultPackageVersions([
      "@nestjs/common",
      "@nestjs/core",
      "@nestjs/platform-express",
      "reflect-metadata",
      "rxjs",
    ], "http-nestjs"),
    files: (context) => withTest({
      "src/app.controller.ts": "import { Controller, Get } from \"@nestjs/common\";\n\n@Controller()\nexport class AppController {\n  @Get(\"health\")\n  health() {\n    return { status: \"ok\" };\n  }\n}\n",
      "src/app.module.ts": "import { Module } from \"@nestjs/common\";\nimport { AppController } from \"./app.controller.js\";\n\n@Module({ controllers: [AppController] })\nexport class AppModule {}\n",
      "src/server.ts": "import \"reflect-metadata\";\nimport { NestFactory } from \"@nestjs/core\";\nimport { AppModule } from \"./app.module.js\";\n\nconst app = await NestFactory.create(AppModule);\nawait app.listen(Number(process.env.PORT ?? 3000));\n",
    }, nestTest(context.profile.tests)),
  },
];

function withTest(
  files: Record<string, string>,
  testFile: string | undefined,
): Record<string, string> {
  return testFile ? { ...files, "test/server.test.ts": testFile } : files;
}

function expressTest(provider: string): string | undefined {
  const setup = "const server = createServer(buildApp());\n  await new Promise<void>((resolve) => server.listen(0, resolve));\n  try {\n    const address = server.address();\n    if (!address || typeof address === \"string\") throw new Error(\"Server did not bind to a TCP port\");\n    const response = await fetch(`http://127.0.0.1:${address.port}/health`);\n    const body = await response.json();";
  const teardown = "  } finally {\n    await new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));\n  }";
  if (provider === "node-test") {
    return `import assert from "node:assert/strict";\nimport { createServer } from "node:http";\nimport test from "node:test";\nimport { buildApp } from "../src/app.ts";\n\ntest("returns service health", async () => {\n  ${setup}\n    assert.equal(response.status, 200);\n    assert.deepEqual(body, { status: "ok" });\n${teardown}\n});\n`;
  }
  if (provider === "vitest" || provider === "jest") {
    const testImport = provider === "vitest" ? 'import { expect, test } from "vitest";\n' : "";
    const sourceExtension = ".js";
    return `import { createServer } from "node:http";\n${testImport}import { buildApp } from "../src/app${sourceExtension}";\n\ntest("returns service health", async () => {\n  ${setup}\n    expect(response.status).toBe(200);\n    expect(body).toEqual({ status: "ok" });\n${teardown}\n});\n`;
  }
  return undefined;
}

function honoTest(provider: string): string | undefined {
  if (provider === "node-test") {
    return "import assert from \"node:assert/strict\";\nimport test from \"node:test\";\nimport { app } from \"../src/app.ts\";\n\ntest(\"returns service health\", async () => {\n  const response = await app.request(\"/health\");\n  assert.equal(response.status, 200);\n  assert.deepEqual(await response.json(), { status: \"ok\" });\n});\n";
  }
  if (provider === "vitest" || provider === "jest") {
    const testImport = provider === "vitest" ? 'import { expect, test } from "vitest";\n' : "";
    const sourceExtension = ".js";
    return `${testImport}import { app } from "../src/app${sourceExtension}";\n\ntest("returns service health", async () => {\n  const response = await app.request("/health");\n  expect(response.status).toBe(200);\n  expect(await response.json()).toEqual({ status: "ok" });\n});\n`;
  }
  return undefined;
}

function nestTest(provider: string): string | undefined {
  if (provider === "node-test") {
    return "import assert from \"node:assert/strict\";\nimport test from \"node:test\";\nimport { AppController } from \"../src/app.controller.ts\";\n\ntest(\"returns service health\", () => {\n  assert.deepEqual(new AppController().health(), { status: \"ok\" });\n});\n";
  }
  if (provider === "vitest" || provider === "jest") {
    const testImport = provider === "vitest" ? 'import { expect, test } from "vitest";\n' : "";
    const sourceExtension = ".js";
    return `${testImport}import { AppController } from "../src/app.controller${sourceExtension}";\n\ntest("returns service health", () => {\n  expect(new AppController().health()).toEqual({ status: "ok" });\n});\n`;
  }
  return undefined;
}

function fastifyFiles(context: Parameters<NonNullable<ProviderContribution["files"]>>[0]): Record<string, string> {
  const validation = validationParts(context.profile.runtime_validation);
  const loggingImport = context.profile.logging === "none"
    ? ""
    : "import { logger } from \"./logger.js\";\n";
  const loggingCall = context.profile.logging === "none"
    ? ""
    : "logger.info({ port }, \"service listening\");\n";
  const files: Record<string, string> = {
    "src/app.ts": `import Fastify from "fastify";\n${validation.importLine}\nexport function buildApp() {\n  const app = Fastify();\n  app.get("/health", async (request) => {\n    ${validation.parseLine}\n    return { status: "ok", name };\n  });\n  return app;\n}\n`,
    "src/server.ts": `import { buildApp } from "./app.js";\n${loggingImport}\nconst port = Number(process.env.PORT ?? 3000);\nconst app = buildApp();\nawait app.listen({ host: "0.0.0.0", port });\n${loggingCall}`,
  };
  const testFile = fastifyTest(context.profile.tests);
  if (testFile) files["test/server.test.ts"] = testFile;
  return files;
}

function validationParts(provider: string): { importLine: string; parseLine: string } {
  if (provider === "zod") {
    return {
      importLine: "import { z } from \"zod\";",
      parseLine: "const { name } = z.object({ name: z.string().default(\"world\") }).parse(request.query);",
    };
  }
  if (provider === "valibot") {
    return {
      importLine: "import { fallback, object, parse, string } from \"valibot\";",
      parseLine: "const { name } = parse(object({ name: fallback(string(), \"world\") }), request.query);",
    };
  }
  return {
    importLine: "",
    parseLine: "const name = typeof (request.query as { name?: unknown }).name === \"string\" ? (request.query as { name: string }).name : \"world\";",
  };
}

function fastifyTest(provider: string): string | undefined {
  const body = `const app = buildApp();\n\nafterAll(() => app.close());\n\ntest("returns service health", async () => {\n  const response = await app.inject({ method: "GET", url: "/health?name=Ada" });\n  expect(response.statusCode).toBe(200);\n  expect(response.json()).toEqual({ status: "ok", name: "Ada" });\n});\n`;
  if (provider === "vitest") {
    return `import { afterAll, expect, test } from "vitest";\nimport { buildApp } from "../src/app.js";\n\n${body}`;
  }
  if (provider === "jest") {
    return `import { buildApp } from "../src/app.js";\n\n${body}`;
  }
  if (provider === "node-test") {
    return "import assert from \"node:assert/strict\";\nimport { after, test } from \"node:test\";\nimport { buildApp } from \"../src/app.ts\";\n\nconst app = buildApp();\nafter(() => app.close());\n\ntest(\"returns service health\", async () => {\n  const response = await app.inject({ method: \"GET\", url: \"/health?name=Ada\" });\n  assert.equal(response.statusCode, 200);\n  assert.deepEqual(response.json(), { status: \"ok\", name: \"Ada\" });\n});\n";
  }
  return undefined;
}
