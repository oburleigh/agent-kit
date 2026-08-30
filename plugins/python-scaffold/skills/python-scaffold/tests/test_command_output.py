import os
import shlex
import sys
from pathlib import Path

import pytest

from python_scaffold.command_output import CommandSession


def test_success_output_is_concise_and_complete_output_is_streamed(
    tmp_path: Path,
) -> None:
    script = tmp_path / "verbose.py"
    script.write_text(
        "import sys\n"
        "for index in range(40): print(f'install line {index}')\n"
        "print('one warning', file=sys.stderr)\n"
    )
    lines: list[str] = []
    session = CommandSession(
        log_directory=tmp_path / "logs",
        identifier="successful-run",
        write_line=lines.append,
    )
    command = (sys.executable, str(script))

    session.run(command, tmp_path)
    session.run(command, tmp_path)
    session.report()

    display = shlex.join(command)
    session_directory = tmp_path / "logs/successful-run"
    assert lines == [
        f"PASS {display}",
        f"PASS {display}",
        f"Full command logs: {session_directory}",
    ]
    assert "install line 0" in (session_directory / "001.stdout.log").read_text()
    assert "one warning" in (session_directory / "001.stderr.log").read_text()
    assert "install line 39" in (session_directory / "002.stdout.log").read_text()
    assert f"$ {display}" in (session_directory / "commands.log").read_text()
    if os.name != "nt":
        assert session_directory.stat().st_mode & 0o777 == 0o700
        assert (session_directory / "001.stdout.log").stat().st_mode & 0o777 == 0o600


def test_failure_reports_bounded_tails_from_both_streams(tmp_path: Path) -> None:
    script = tmp_path / "failure.py"
    script.write_text(
        "import sys\n"
        "print('diagnostic stdout')\n"
        "for index in range(40): print(f'warning {index}', file=sys.stderr)\n"
        "raise SystemExit(2)\n"
    )
    session = CommandSession(
        log_directory=tmp_path / "logs",
        identifier="failed-run",
        write_line=lambda _line: None,
    )
    command = (sys.executable, str(script))

    with pytest.raises(RuntimeError) as caught:
        session.run(command, tmp_path)

    session_directory = tmp_path / "logs/failed-run"
    failure = str(caught.value)
    assert f"Command failed: {shlex.join(command)} (exit 2)" in failure
    assert "diagnostic stdout" in failure
    assert "warning 0" not in failure
    assert "warning 39" in failure
    assert f"Full command logs: {session_directory}" in failure
    assert "diagnostic stdout" in (session_directory / "001.stdout.log").read_text()
    assert "warning 0" in (session_directory / "001.stderr.log").read_text()
