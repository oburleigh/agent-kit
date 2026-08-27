import { lstat } from "node:fs/promises";

export type TargetState = "absent";

export async function assertTargetAvailable(target: string): Promise<TargetState> {
  try {
    const targetStat = await lstat(target);
    if (targetStat.isSymbolicLink()) {
      throw new Error(`Target is a symbolic link: ${target}`);
    }
    throw new Error(`Target already exists: ${target}`);
  } catch (error) {
    if (isMissingPath(error)) {
      return "absent";
    }
    throw error;
  }
}

function isMissingPath(error: unknown): error is NodeJS.ErrnoException {
  return error instanceof Error && "code" in error && error.code === "ENOENT";
}
