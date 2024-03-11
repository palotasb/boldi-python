import os
import shlex
import subprocess
import sys
from contextlib import AbstractContextManager, ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Any, Callable, Iterable, List, Mapping, MutableMapping, TextIO, TypedDict, Union

from typing_extensions import Self, Unpack

SubprocessInput = int
SubprocessFile = Union[IO, SubprocessInput]


class RunArgs(TypedDict, total=False):
    bufsize: int
    capture_output: bool
    check: bool
    close_fds: bool
    cwd: Path
    encoding: str
    env: Mapping[str, str]
    errors: Any
    extra_groups: Iterable[str | int]
    group: str | int
    input: IO
    pipesize: int
    preexec_fn: Callable[..., Any]
    process_group: int
    shell: bool
    startupinfo: Any
    stderr: SubprocessFile
    stdin: SubprocessFile
    stdout: SubprocessFile
    text: bool
    timeout: float
    umask: int
    universal_newlines: bool
    user: str | int


def split_args(*arg_groups: Union[str, List[Any]]) -> List[str]:
    return [str(sub_arg) for args in arg_groups for sub_arg in (shlex.split(args) if isinstance(args, str) else args)]


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

    def run(self, *args: Union[str, List[Any]], **kwargs: Unpack[RunArgs]) -> subprocess.CompletedProcess:
        kwargs.setdefault("check", True)
        kwargs.setdefault("text", True)
        kwargs.setdefault("cwd", self.cwd)
        kwargs.setdefault("env", self.env)
        if not kwargs.get("capture_output"):
            kwargs.setdefault("stdin", self.stdin)
            kwargs.setdefault("stdout", self.stdout)
            kwargs.setdefault("stderr", self.stderr)
        args_list = split_args(*args)
        return subprocess.run(args_list, **kwargs)

    def run_py(self, *args: Union[str, List[Any]], **kwargs: Unpack[RunArgs]) -> subprocess.CompletedProcess:
        return self.run([sys.executable], *args, **kwargs)
