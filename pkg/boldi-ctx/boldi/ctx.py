from __future__ import annotations

import os
import subprocess
import sys
from contextlib import AbstractContextManager, ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, MutableMapping, TextIO, Union

from typing_extensions import Self, Unpack

from boldi.proc import RunArgs, run as _run, run_py as _run_py


@dataclass
class Ctx(AbstractContextManager):
    """
    Represents a context where the values in this object should apply.

    When a `Ctx` object is passed as an argument to a function,
    or defined as a base class or a `self` attribute of an object,
    then the values in the `Ctx` object should be used explicitly
    instead of the original default values that they replace.

    Examples:
        If a `ctx: Ctx` or `self.ctx: Ctx` is present,
        always explicitly `print(..., file=ctx.stdout)`
        instead of a `print(...)` (that defaults to `sys.stdout`).
    """

    stack: ExitStack = field(default_factory=ExitStack)
    """An [`ExitStack`][contextlib.ExitStack] provided for convenience."""

    stdin: TextIO = field(default_factory=lambda: sys.stdin)
    """Replacement for [`sys.stdin`][]."""

    stdout: TextIO = field(default_factory=lambda: sys.stdout)
    """Replacement for [`sys.stdout`][]."""

    stderr: TextIO = field(default_factory=lambda: sys.stderr)
    """Replacement for [`sys.stderr`][]."""

    argv: list[str] = field(default_factory=lambda: sys.argv)
    """Replacement for [`sys.argv`][]."""

    env: MutableMapping[str, str] = field(default_factory=lambda: os.environ)
    """Replacement for [`os.environ`][]."""

    cwd: Path = field(default_factory=Path.cwd)
    """Replacement for [`pathlib.Path.cwd`][]."""

    def __enter__(self) -> Self:
        """Enter the context of `self.stack`."""
        self.stack.__enter__()
        return self

    def __exit__(self, *exc_info) -> bool:
        """Exit the context of `self.stack`."""
        return self.stack.__exit__(*exc_info)

    def _set_run_kwargs(self, **kwargs: Unpack[RunArgs]):
        kwargs.setdefault("cwd", self.cwd)
        kwargs.setdefault("env", self.env)
        if not kwargs.get("capture_output"):
            kwargs.setdefault("stdin", self.stdin)
            kwargs.setdefault("stdout", self.stdout)
            kwargs.setdefault("stderr", self.stderr)

    def run(self, *arg_groups: Union[str, List[Any]], **kwargs: Unpack[RunArgs]) -> subprocess.CompletedProcess:
        """
        Run a subprocess using the provided command line arguments and updated defaults.

        Args:
            arg_groups: Groups of command line arguments, provided as positional arguments.
                As defined in [`boldi.proc.split_args`][].
            kwargs: Arguments to [`subprocess.run`][].
                Defaults to `check=True`, `text=True`, and values set in `self.{stdin,stdout,stderr,env,cwd}`,
                unless otherwise set by the caller.

        Returns:
            Completed process object.
        """
        self._set_run_kwargs(**kwargs)
        return _run(*arg_groups, **kwargs)

    def run_py(self, *arg_groups: Union[str, List[Any]], **kwargs: Unpack[RunArgs]) -> subprocess.CompletedProcess:
        """
        Run a subprocess using the current Python interpreter, the provided command line arguments and updated defaults.

        Args:
            arg_groups: Groups of command line arguments, provided as positional arguments.
                As defined in [`boldi.proc.split_args`][].
            kwargs: Arguments to [`subprocess.run`][]. As defined in [`run`][boldi.ctx.Ctx.run].

        Returns:
            Completed process object.
        """
        self._set_run_kwargs(**kwargs)
        return _run_py(*arg_groups, **kwargs)
