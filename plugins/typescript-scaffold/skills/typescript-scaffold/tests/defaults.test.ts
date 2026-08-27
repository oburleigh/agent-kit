import { describe, expect, test } from "vitest";
import { loadScaffoldDefaults } from "../src/defaults.js";

const validDefaults = `
schema_version: 1
generated_package_version: 0.1.0
runtime:
  node_version: "24"
  typescript_target: ES2023
package_managers:
  pnpm: 11.24.0
  npm: 11.17.0
  yarn: 4.18.0
  bun: 1.3.14
packages:
  fastify: ^5.12.1
framework_generators:
  create-vite: 9.2.0
ci:
  runner: ubuntu-latest
  actions:
    checkout: actions/checkout@v4
    setup_node: actions/setup-node@v4
    setup_bun: oven-sh/setup-bun@v2
    setup_pnpm: pnpm/action-setup@v4
    gitleaks: gitleaks/gitleaks-action@v2
  images:
    node: node
    bun: oven/bun
    gitleaks: zricethezav/gitleaks:v8.30.1
`;

describe("scaffold defaults", () => {
  test("loads the release-owned version and CI policy", () => {
    const defaults = loadScaffoldDefaults(validDefaults);

    expect(defaults).toMatchObject({
      generated_package_version: "0.1.0",
      runtime: { node_version: "24", typescript_target: "ES2023" },
      packages: { fastify: "^5.12.1" },
      framework_generators: { "create-vite": "9.2.0" },
      ci: {
        runner: "ubuntu-latest",
        actions: { checkout: "actions/checkout@v4" },
        images: { node: "node" },
      },
    });
  });

  test("rejects an incomplete defaults catalog with a useful field path", () => {
    const invalidDefaults = validDefaults.replace('  node_version: "24"\n', "");

    expect(() => loadScaffoldDefaults(invalidDefaults))
      .toThrow(/runtime\.node_version/);
  });

  test("rejects malformed versions and unknown fields", () => {
    const invalidVersion = validDefaults.replace("fastify: ^5.12.1", "fastify: soon");
    const unknownField = `${validDefaults}\nlegacy_defaults: true\n`;

    expect(() => loadScaffoldDefaults(invalidVersion)).toThrow(/packages\.fastify/);
    expect(() => loadScaffoldDefaults(unknownField)).toThrow(/Unrecognized key/);
  });

  test("rejects malformed CI action and image references", () => {
    const invalidAction = validDefaults.replace(
      "actions/checkout@v4",
      "actions/checkout-v4",
    );
    const invalidImage = validDefaults.replace("node: node", "node: https://node");

    expect(() => loadScaffoldDefaults(invalidAction)).toThrow(/ci\.actions\.checkout/);
    expect(() => loadScaffoldDefaults(invalidImage)).toThrow(/ci\.images\.node/);
  });

  test("rejects tags on images whose tags are derived during generation", () => {
    const taggedNode = validDefaults.replace("node: node", "node: node:24");
    const taggedBun = validDefaults.replace("bun: oven/bun", "bun: oven/bun:1.3.14");

    expect(() => loadScaffoldDefaults(taggedNode)).toThrow(/ci\.images\.node/);
    expect(() => loadScaffoldDefaults(taggedBun)).toThrow(/ci\.images\.bun/);
  });

  test("requires a tag on the Gitleaks image emitted verbatim", () => {
    const untaggedGitleaks = validDefaults.replace(
      "gitleaks: zricethezav/gitleaks:v8.30.1",
      "gitleaks: zricethezav/gitleaks",
    );

    expect(() => loadScaffoldDefaults(untaggedGitleaks))
      .toThrow(/ci\.images\.gitleaks/);
  });
});
