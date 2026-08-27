from pathlib import PurePosixPath, PureWindowsPath


def require_normalized_relative_path(value: str) -> str:
    path = PurePosixPath(value)
    windows_path = PureWindowsPath(value)
    if (
        not value
        or value == "."
        or "\\" in value
        or path.is_absolute()
        or windows_path.drive
        or ".." in path.parts
        or path.as_posix() != value
    ):
        raise ValueError(f"Expected a normalized relative path, got: {value}")
    return value
