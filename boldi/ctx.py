import sys
import os
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO, MutableMapping


@dataclass
class Ctx:
    stack: ExitStack = field(default_factory=ExitStack)
    stdin: TextIO = field(default_factory=lambda: sys.stdin)
    stdout: TextIO = field(default_factory=lambda: sys.stdout)
    stderr: TextIO = field(default_factory=lambda: sys.stderr)
    env: MutableMapping[str, str] = field(default_factory=lambda: os.environ)
    cwd: Path = field(default_factory=Path.cwd)
