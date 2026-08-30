import { mkdtemp, readFile, stat, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, test } from "vitest";
import { createCommandSession } from "../src/command-output.js";

describe("command output", () => {
  test("prints concise results while streaming complete output to private logs", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-command-output-"));
    const logDirectory = join(root, "logs");
    const script = join(root, "verbose.mjs");
    await writeFile(
      script,
      "for (let index = 0; index < 40; index++) console.log(`install line ${index}`);\n"
        + 'console.error("one warning");\n',
    );
    const lines: string[] = [];
    const session = createCommandSession({
      logDirectory,
      identifier: "successful-run",
      writeLine: (line) => lines.push(line),
    });

    const captured = await session.readStdout(process.execPath, [script], { cwd: root });
    await session.run(process.execPath, [script], { cwd: root });
    session.report();

    const display = `${process.execPath} ${script}`;
    const sessionDirectory = join(logDirectory, "successful-run");
    expect(lines).toEqual([
      `PASS ${display}`,
      `PASS ${display}`,
      `Full command logs: ${sessionDirectory}`,
    ]);
    expect(captured).toContain("install line 39");
    expect(await readFile(join(sessionDirectory, "001.stdout.log"), "utf8"))
      .toContain("install line 0");
    expect(await readFile(join(sessionDirectory, "001.stderr.log"), "utf8"))
      .toContain("one warning");
    expect(await readFile(join(sessionDirectory, "002.stdout.log"), "utf8"))
      .toContain("install line 39");
    expect(await readFile(join(sessionDirectory, "commands.log"), "utf8"))
      .toContain(`$ ${display}`);
    if (process.platform !== "win32") {
      expect((await stat(sessionDirectory)).mode & 0o777).toBe(0o700);
      expect((await stat(join(sessionDirectory, "001.stdout.log"))).mode & 0o777)
        .toBe(0o600);
    }
  });

  test("keeps a bounded diagnostic tail from both output streams", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-kit-command-failure-"));
    const logDirectory = join(root, "logs");
    const script = join(root, "failure.mjs");
    await writeFile(
      script,
      'console.log("diagnostic stdout");\n'
        + 'for (let index = 0; index < 40; index++) console.error(`warning ${index}`);\n'
        + "process.exit(2);\n",
    );
    const session = createCommandSession({
      logDirectory,
      identifier: "failed-run",
      writeLine: () => undefined,
    });

    const failure = await session.run(process.execPath, [script], { cwd: root })
      .then(() => "", (error: unknown) => error instanceof Error ? error.message : String(error));

    const sessionDirectory = join(logDirectory, "failed-run");
    expect(failure).toContain(`Command failed: ${process.execPath} ${script} (exit 2)`);
    expect(failure).toContain("diagnostic stdout");
    expect(failure).not.toContain("warning 0");
    expect(failure).toContain("warning 39");
    expect(failure).toContain(`Full command logs: ${sessionDirectory}`);
    expect(await readFile(join(sessionDirectory, "001.stdout.log"), "utf8"))
      .toContain("diagnostic stdout");
    expect(await readFile(join(sessionDirectory, "001.stderr.log"), "utf8"))
      .toContain("warning 0");
  });
});
