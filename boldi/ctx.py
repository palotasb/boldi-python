import os
import sys
from contextlib import AbstractContextManager, ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from typing import MutableMapping, TextIO

from typing_extensions import Self


@dataclass
class Ctx(AbstractContextManager):
    stack: ExitStack = field(default_factory=ExitStack)
    stdin: TextIO = field(default_factory=lambda: sys.stdin)
    stdout: TextIO = field(default_factory=lambda: sys.stdout)
    stderr: TextIO = field(default_factory=lambda: sys.stderr)
    argv: list[str] = field(default_factory=lambda: sys.argv)
    env: MutableMapping[str, str] = field(default_factory=lambda: os.environ)
    cwd: Path = field(default_factory=Path.cwd)

    def __enter__(self) -> Self:
        self.stack.__enter__()
        return self

    def __exit__(self, *exc_info) -> bool:
        return self.stack.__exit__(*exc_info)
