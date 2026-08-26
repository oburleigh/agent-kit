import { mkdtemp, mkdir, symlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, test } from "vitest";

async function loadProfileModule() {
  return import("../src/profile.js");
}

async function loadTargetModule() {
  return import("../src/target.js");
}

describe("profile validation", () => {
  test("accepts a fully materialized service profile", async () => {
    const { loadProfileText } = await loadProfileModule();
    const profile = loadProfileText(`
schema_version: 1
name: service
preset: service
package_manager: npm
package_manager_version: 11.17.0
module: esm
build: tsc
quality: biome
tests: vitest
runtime_validation: zod
http: fastify
logging: pino
hooks: none
ci: github-actions
publishing: none
workspace: none
secret_scan: gitleaks
duplication: jscpd
framework: none
license: apache-2.0
install_dependencies: false
run_quality_gates: false
initialize_git: false
default_author: Example Maintainer
package_versions: {}
extra_dependencies: []
extra_dev_dependencies: []
extra_scripts: {}
ci_commands: []
`);

    expect(profile.name).toBe("service");
    expect(profile.http).toBe("fastify");
  });

  test("rejects unknown providers at the profile boundary", async () => {
    const { loadProfileText } = await loadProfileModule();

    expect(() => loadProfileText(`schema_version: 1\nname: bad\npreset: service\nhttp: bespoke-server`))
      .toThrow(/http/);
  });

  test("accepts per-run project metadata in an execution profile", async () => {
    const { loadProfileText } = await loadProfileModule();
    const profile = loadProfileText(`
schema_version: 1
name: execution
preset: cli
package_manager: npm
package_manager_version: 11.17.0
module: esm
build: tsup
quality: none
tests: none
runtime_validation: none
http: none
logging: none
hooks: none
ci: none
publishing: none
workspace: none
secret_scan: none
duplication: none
framework: none
license: apache-2.0
install_dependencies: false
run_quality_gates: false
initialize_git: false
default_author: Default Maintainer
project:
  name: release-tool
  description: Publishes release artifacts.
  author: Project Maintainer
  repository_url: https://github.com/example/release-tool.git
package_versions: {}
extra_dependencies: []
extra_dev_dependencies: []
extra_scripts: {}
ci_commands: []
`);

    expect(profile.project).toEqual({
      name: "release-tool",
      description: "Publishes release artifacts.",
      author: "Project Maintainer",
      repository_url: "https://github.com/example/release-tool.git",
    });
  });
});

describe("target safety", () => {
  test("rejects a non-empty target", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-target-"));
    const target = join(root, "existing");
    await mkdir(target);
    await writeFile(join(target, "owned.txt"), "keep me");
    const { assertTargetAvailable } = await loadTargetModule();

    await expect(assertTargetAvailable(target)).rejects.toThrow(/already exists/);
  });

  test("rejects an empty target", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-empty-target-"));
    const target = join(root, "existing");
    await mkdir(target);
    const { assertTargetAvailable } = await loadTargetModule();

    await expect(assertTargetAvailable(target)).rejects.toThrow(/already exists/);
  });

  test("rejects a target that is a symbolic link", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-target-link-"));
    const backingDirectory = join(root, "backing");
    const target = join(root, "target");
    await mkdir(backingDirectory);
    await symlink(backingDirectory, target, "dir");
    const { assertTargetAvailable } = await loadTargetModule();

    await expect(assertTargetAvailable(target)).rejects.toThrow(/symbolic link/);
  });
});
