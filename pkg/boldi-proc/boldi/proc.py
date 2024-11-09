import shlex
import subprocess
import sys
from pathlib import Path
from typing import IO, Any, Callable, Iterable, List, Mapping, TypedDict, Union

from typing_extensions import Unpack


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
    input: str | None
    pipesize: int
    preexec_fn: Callable[..., Any]
    process_group: int
    shell: bool
    startupinfo: Any
    stderr: IO | int
    stdin: IO | int
    stdout: IO | int
    text: bool
    timeout: float
    umask: int
    universal_newlines: bool
    user: str | int


def args_iter(*args: Union[str, List[Any]]) -> Iterable[str]:
    """
    Split mixed and/or quoted command line arguments into a simple list of arguments.

    Args:
        args: Command line arguments, provided as positional arguments.
            Each argument is processed differently depending on its type.
            Strings are split using [`shlex.split`][] into further arguments.
            Lists are replaced by their contents (each item converted to a string).
            Other types are converted to strings using [`str`][].

    Returns:
        A flat list of command line arguments.

    Examples:
        Common use cases:

        ```py
        result = ["prog", "-a=b", "d e", "f"]
        assert list(args_iter("prog -a=b 'd e' f")) == result
        assert list(args_iter("prog -a=b", ["d e"], "f")) == result
        ```

        Any argument can be given either as a string or a list,
        and they can be combined arbitrarily:

        ```py
        result = ["prog", "-a=b", "d e", "f"]
        assert list(args_iter("prog -a=b", "'d e' f")) == result
        assert list(args_iter("prog", "-a=b", '"d e"', "f")) == result
        assert list(args_iter(["prog", "-a=b", "d e", "f"])) == result
        ```
    """
    for arg in args:
        if isinstance(arg, str):
            yield from shlex.split(arg)
        elif isinstance(arg, list):
            yield from (str(sub_arg) for sub_arg in arg)
        else:
            yield str(arg)


def run(*args: Union[str, List[Any]], **kwargs: Unpack[RunArgs]) -> subprocess.CompletedProcess:
    """
    Run a subprocess using the provided command line arguments and updated defaults.

    Args:
        args: Command line arguments, provided as positional arguments.
            As defined in [`args_iter`][boldi.proc.args_iter].
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
    args_list = list(args_iter(*args))
    return subprocess.run(args_list, **kwargs)


def run_py(*args: Union[str, List[Any]], **kwargs: Unpack[RunArgs]) -> subprocess.CompletedProcess:
    """
    Run a subprocess using the current Python interpreter, the provided command line arguments and updated defaults.

    Args:
        args: Command line arguments, provided as positional arguments.
            As defined in [`args_iter`][boldi.proc.args_iter].
        kwargs: Arguments to [`subprocess.run`][]. As defined in [`run`][boldi.proc.run].

    Returns:
        Completed process object.
    """
    return run([sys.executable], *args, **kwargs)
