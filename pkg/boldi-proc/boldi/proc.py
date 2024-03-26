import shlex
import subprocess
import sys
from pathlib import Path
from typing import IO, Any, Callable, Iterable, List, Mapping, TypedDict, Union

from typing_extensions import Unpack

SubprocessInput = int
"""Type definition for the predefined values for file descriptors in the [`subprocess`][] module."""

SubprocessFile = Union[IO, int]
"""Type definition for the file descriptor arguments for [`RunArgs`][boldi.proc.RunArgs]."""


class RunArgs(TypedDict, total=False):
    """
    Arguments to [`subprocess.run`][] or [`subprocess.Popen`][].
    """

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
    """
    Flatten groups of command line arguments into a simple list of arguments.

    Args:
        arg_groups: Groups of command line arguments, provided as positional arguments.
            Each "arg group" is either a string or a sub-list of arbitrary objects.
            Strings are split using [`shlex.split`][] into further arguments.
            Sub-list items are converted to [`str`][], but not split further.

    Returns:
        A flat list of command line arguments.

    Examples:
        Common use cases:

        ```py
        result = ["prog", "-a=b", "d e", "f"]
        assert split_args("prog -a=b 'd e' f") == result
        assert split_args("prog -a=b", ["d e"], "f") == result
        ```

        Any argument can be given either as a string or a list,
        and they can be combined arbitrarily:

        ```py
        result = ["prog", "-a=b", "d e", "f"]
        assert split_args("prog -a=b", "'d e' f") == result
        assert split_args("prog", "-a=b", '"d e"', "f") == result
        assert split_args(["prog", "-a=b", "d e", "f"]) == result
        ```
    """
    return [str(sub_arg) for args in arg_groups for sub_arg in (shlex.split(args) if isinstance(args, str) else args)]


def run(*arg_groups: Union[str, List[Any]], **kwargs: Unpack[RunArgs]) -> subprocess.CompletedProcess:
    """
    Run a subprocess using the provided command line arguments and updated defaults.

    Args:
        arg_groups: Groups of command line arguments, provided as positional arguments.
            As defined in [`split_args`][boldi.proc.split_args].
        kwargs: Arguments to [`subprocess.run`][].
            Defaults to `check=True`, `text=True`, and connecting to `sys.{stdin, stdout, stderr}`,
            unless otherwise set by the caller.

    Returns:
        Completed process object.
    """
    kwargs.setdefault("check", True)
    kwargs.setdefault("text", True)
    if not kwargs.get("capture_output"):
        kwargs.setdefault("stdin", sys.stdin)
        kwargs.setdefault("stdout", sys.stdout)
        kwargs.setdefault("stderr", sys.stderr)
    args_list = split_args(*arg_groups)
    return subprocess.run(args_list, **kwargs)


def run_py(*arg_groups: Union[str, List[Any]], **kwargs: Unpack[RunArgs]) -> subprocess.CompletedProcess:
    """
    Run a subprocess using the current Python interpreter, the provided command line arguments and updated defaults.

    Args:
        arg_groups: Groups of command line arguments, provided as positional arguments.
            As defined in [`split_args`][boldi.proc.split_args].
        kwargs: Arguments to [`subprocess.run`][]. As defined in [`run`][boldi.proc.run].

    Returns:
        Completed process object.
    """
    return run([sys.executable], *arg_groups, **kwargs)
