import os
import shutil
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from tempfile import mkdtemp

from atomicswap import swap


class TargetExistsError(FileExistsError):
    pass


def create_only(target: Path, build: Callable[[Path], None]) -> Path:
    target = target.expanduser().absolute()
    if os.path.lexists(target):
        raise TargetExistsError(f"Target already exists: {target}")
    if not target.parent.is_dir():
        raise FileNotFoundError(f"Target parent does not exist: {target.parent}")

    staging = Path(mkdtemp(prefix=f".{target.name}-", dir=target.parent))
    claimed = False
    try:
        build(staging)
        try:
            target.mkdir()
            claimed = True
        except FileExistsError as error:
            raise TargetExistsError(f"Target was created during generation: {target}") from error
        swap(staging, target)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        if claimed:
            with suppress(OSError):
                target.rmdir()
        raise
    shutil.rmtree(staging, ignore_errors=True)
    return target
