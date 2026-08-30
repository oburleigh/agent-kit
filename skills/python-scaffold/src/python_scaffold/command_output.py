import os
import shlex
import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from platformdirs import user_log_path

FAILURE_TAIL_LINES = 20
FAILURE_TAIL_BYTES = 64 * 1024


class CommandSession:
    def __init__(
        self,
        *,
        log_directory: Path | None = None,
        identifier: str | None = None,
        write_line: Callable[[str], None] = print,
    ) -> None:
        directory = log_directory or command_log_directory()
        self.directory = directory / (identifier or str(uuid4()))
        self._write_line = write_line
        self._command_count = 0
        self._reported = False

    def run(self, command: tuple[str, ...], cwd: Path) -> None:
        self._command_count += 1
        prefix = f"{self._command_count:03d}"
        display = shlex.join(command)
        stdout_path = self.directory / f"{prefix}.stdout.log"
        stderr_path = self.directory / f"{prefix}.stderr.log"
        index_path = self.directory / "commands.log"
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._append_private(
            index_path,
            "\n".join(
                [
                    f"[{prefix}]",
                    f"$ {display}",
                    f"cwd: {cwd}",
                    f"stdout: {stdout_path}",
                    f"stderr: {stderr_path}",
                    "",
                ]
            ),
        )

        try:
            with (
                self._open_private(stdout_path) as stdout,
                self._open_private(stderr_path) as stderr,
            ):
                process = subprocess.Popen(command, cwd=cwd, stdout=stdout, stderr=stderr)
                exit_code = process.wait()
        except OSError as error:
            self._append_private(index_path, "exit: unavailable\n\n")
            self._reported = True
            raise RuntimeError(
                self._failure_message(display, None, stdout_path, stderr_path, str(error))
            ) from error

        self._append_private(index_path, f"exit: {exit_code}\n\n")
        if exit_code != 0:
            self._reported = True
            raise RuntimeError(self._failure_message(display, exit_code, stdout_path, stderr_path))
        self._write_line(f"PASS {display}")

    def report(self) -> None:
        if self._command_count > 0 and not self._reported:
            self._reported = True
            self._write_line(f"Full command logs: {self.directory}")

    def _failure_message(
        self,
        command: str,
        exit_code: int | None,
        stdout_path: Path,
        stderr_path: Path,
        fallback: str = "",
    ) -> str:
        stdout_tail = self._read_tail(stdout_path)
        stderr_tail = self._read_tail(stderr_path)
        details = [
            section
            for section in (
                f"[stdout tail]\n{stdout_tail}" if stdout_tail else "",
                f"[stderr tail]\n{stderr_tail}" if stderr_tail else "",
            )
            if section
        ]
        if not details:
            details.append(fallback or "No command output captured.")
        status = exit_code if exit_code is not None else "unavailable"
        return "\n".join(
            [
                f"Command failed: {command} (exit {status})",
                *details,
                f"Full command logs: {self.directory}",
            ]
        )

    @staticmethod
    def _open_private(path: Path) -> BinaryIO:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        return os.fdopen(descriptor, "wb")

    @staticmethod
    def _append_private(path: Path, content: str) -> None:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(descriptor, "a", encoding="utf-8") as log:
            log.write(content)

    @staticmethod
    def _read_tail(path: Path) -> str:
        if not path.exists():
            return ""
        with path.open("rb") as log:
            log.seek(0, os.SEEK_END)
            length = min(log.tell(), FAILURE_TAIL_BYTES)
            if length == 0:
                return ""
            log.seek(-length, os.SEEK_END)
            output = log.read().decode("utf-8", errors="replace")
        return "\n".join(output.splitlines()[-FAILURE_TAIL_LINES:])


def command_log_directory(environment: Mapping[str, str] = os.environ) -> Path:
    configured = environment.get("AGENT_KIT_LOG_DIR")
    root = Path(configured).expanduser() if configured else user_log_path("agent-kit")
    return root / "scaffolds/python"
