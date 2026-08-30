import { appendFile, mkdir, open } from "node:fs/promises";
import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { join } from "node:path";
import envPaths from "env-paths";

const FAILURE_TAIL_LINES = 20;
const FAILURE_TAIL_BYTES = 64 * 1024;

export type CommandRunner = (
  command: string,
  args: string[],
  options: { cwd: string },
) => Promise<void>;

interface CommandSessionOptions {
  logDirectory?: string;
  identifier?: string;
  writeLine?: (line: string) => void;
}

interface LoggedCommand {
  display: string;
  stdoutPath: string;
  stderrPath: string;
}

class LoggedCommandError extends Error {}

export interface CommandSession {
  run: CommandRunner;
  readStdout(command: string, args: string[], options: { cwd: string }): Promise<string>;
  report(): void;
}

export function createCommandSession(
  options: CommandSessionOptions = {},
): CommandSession {
  const logDirectory = options.logDirectory ?? resolveCommandLogDirectory();
  const sessionDirectory = join(logDirectory, options.identifier ?? randomUUID());
  const writeLine = options.writeLine ?? ((line: string) => console.log(line));
  let commandCount = 0;
  let reported = false;

  const execute = async (
    command: string,
    args: string[],
    commandOptions: { cwd: string },
  ): Promise<LoggedCommand> => {
    commandCount += 1;
    try {
      return await executeLoggedCommand(
        command,
        args,
        commandOptions,
        sessionDirectory,
        commandCount,
        writeLine,
      );
    } catch (error) {
      if (error instanceof LoggedCommandError) reported = true;
      throw error;
    }
  };

  return {
    async run(command, args, commandOptions) {
      await execute(command, args, commandOptions);
    },
    async readStdout(command, args, commandOptions) {
      const logged = await execute(command, args, commandOptions);
      return readTail(logged.stdoutPath);
    },
    report() {
      if (commandCount > 0 && !reported) {
        reported = true;
        writeLine(`Full command logs: ${sessionDirectory}`);
      }
    },
  };
}

export function resolveCommandLogDirectory(
  environment: NodeJS.ProcessEnv = process.env,
): string {
  const root = environment.AGENT_KIT_LOG_DIR
    ?? envPaths("agent-kit", { suffix: "" }).log;
  return join(root, "scaffolds", "typescript");
}

async function executeLoggedCommand(
  command: string,
  args: string[],
  options: { cwd: string },
  sessionDirectory: string,
  commandNumber: number,
  writeLine: (line: string) => void,
): Promise<LoggedCommand> {
  await mkdir(sessionDirectory, { recursive: true, mode: 0o700 });
  const prefix = String(commandNumber).padStart(3, "0");
  const stdoutPath = join(sessionDirectory, `${prefix}.stdout.log`);
  const stderrPath = join(sessionDirectory, `${prefix}.stderr.log`);
  const display = formatCommand(command, args);
  const indexPath = join(sessionDirectory, "commands.log");
  await appendPrivateFile(indexPath, [
    `[${prefix}]`,
    `$ ${display}`,
    `cwd: ${options.cwd}`,
    `stdout: ${stdoutPath}`,
    `stderr: ${stderrPath}`,
  ].join("\n") + "\n");

  const stdout = await open(stdoutPath, "wx", 0o600);
  let stderr;
  try {
    stderr = await open(stderrPath, "wx", 0o600);
  } catch (error) {
    await stdout.close();
    throw error;
  }

  let commandError: unknown;
  try {
    await spawnCommand(command, args, options.cwd, stdout.fd, stderr.fd);
  } catch (error) {
    commandError = error;
  } finally {
    await Promise.all([stdout.close(), stderr.close()]);
  }

  if (commandError) {
    const error = commandError;
    const exitCode = errorNumber(error, "exitCode");
    await appendPrivateFile(indexPath, `exit: ${exitCode ?? "unavailable"}\n\n`);
    const [stdoutTail, stderrTail] = await Promise.all([
      readTail(stdoutPath),
      readTail(stderrPath),
    ]);
    throw new LoggedCommandError(
      failureMessage(display, exitCode, stdoutTail, stderrTail, error, sessionDirectory),
      { cause: error },
    );
  }

  await appendPrivateFile(indexPath, "exit: 0\n\n");
  writeLine(`PASS ${display}`);
  return { display, stdoutPath, stderrPath };
}

async function appendPrivateFile(path: string, content: string): Promise<void> {
  await appendFile(path, content, { encoding: "utf8", mode: 0o600 });
}

async function spawnCommand(
  command: string,
  args: string[],
  cwd: string,
  stdout: number,
  stderr: number,
): Promise<void> {
  const child = spawn(command, args, {
    cwd,
    stdio: ["ignore", stdout, stderr],
    windowsHide: true,
  });
  await new Promise<void>((resolve, reject) => {
    child.once("error", reject);
    child.once("close", (exitCode, signal) => {
      if (exitCode === 0) {
        resolve();
        return;
      }
      reject(Object.assign(
        new Error(signal ? `Command terminated by ${signal}` : `Command exited with ${exitCode}`),
        { exitCode: exitCode ?? undefined },
      ));
    });
  });
}

async function readTail(path: string): Promise<string> {
  const file = await open(path, "r");
  try {
    const metadata = await file.stat();
    const length = Math.min(metadata.size, FAILURE_TAIL_BYTES);
    if (length === 0) return "";
    const buffer = Buffer.alloc(length);
    await file.read(buffer, 0, length, metadata.size - length);
    return buffer.toString("utf8").trimEnd()
      .split(/\r?\n/).slice(-FAILURE_TAIL_LINES).join("\n");
  } finally {
    await file.close();
  }
}

function failureMessage(
  command: string,
  exitCode: number | undefined,
  stdoutTail: string,
  stderrTail: string,
  error: unknown,
  sessionDirectory: string,
): string {
  const details = [
    stdoutTail ? `[stdout tail]\n${stdoutTail}` : "",
    stderrTail ? `[stderr tail]\n${stderrTail}` : "",
  ].filter(Boolean);
  if (details.length === 0) details.push(shortError(error));
  return [
    `Command failed: ${command} (exit ${exitCode ?? "unavailable"})`,
    ...details,
    `Full command logs: ${sessionDirectory}`,
  ].join("\n");
}

function shortError(error: unknown): string {
  if (error && typeof error === "object") {
    const shortMessage = Reflect.get(error, "shortMessage");
    if (typeof shortMessage === "string") return shortMessage;
  }
  return error instanceof Error ? error.message : String(error);
}

function errorNumber(error: unknown, key: string): number | undefined {
  if (!error || typeof error !== "object") return undefined;
  const value = Reflect.get(error, key);
  return typeof value === "number" ? value : undefined;
}

function formatCommand(command: string, args: string[]): string {
  return [command, ...args].map(formatArgument).join(" ");
}

function formatArgument(value: string): string {
  return /^[a-zA-Z0-9_./:@%+=,-]+$/.test(value) ? value : JSON.stringify(value);
}
