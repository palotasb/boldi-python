from argparse import ArgumentError, ArgumentParser
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import partial, partialmethod
from inspect import signature
from pathlib import Path
from sys import exit

from rich.console import Console
from rich.markup import escape as rich_escape
from rich.theme import Theme
from rich.traceback import Traceback

import boldi.plugins
from boldi.ctx import Ctx

_THEME = Theme(
    {
        "info": "blue",
        "pass": "green",
        "PASS": "bold green",
        "warn": "yellow",
        "WARN": "bold yellow",
        "fail": "red",
        "FAIL": "bold bright_red",
        "traceback.border": "yellow",
    }
)


class _CliCtxDefaultConsole(Console):
    """Implementation detail used to set a default value for [boldi.cli.CliCtx.console][]."""

    pass


class CliUsageException(Exception):
    """Raised when a CLI usage error is encountered."""

    pass


@dataclass
class CliCtx(Ctx):
    """Extends [`Ctx`][boldi.ctx.Ctx] with a console feature for rich CLI output."""

    console: Console = field(default_factory=_CliCtxDefaultConsole)
    """A rich console that outputs to `self.stderr` by default."""

    parser: ArgumentParser = field(default_factory=ArgumentParser)
    """The root [`argparse.ArgumentParser`][] for the `boldi` CLI."""

    verbose: bool = field(default=False)
    """Whether to enable verbose output."""

    def __post_init__(self):
        if isinstance(self.console, _CliCtxDefaultConsole):
            self.console = Console(file=self.stderr, theme=_THEME, highlight=False)

    def msg(self, *args, **kwargs):
        """Prints a message to `self.console`."""
        self.console.print(*args, **kwargs)

    msg_info = partialmethod(msg, style="info")
    msg_pass = partialmethod(msg, style="pass")
    msg_PASS = partialmethod(msg, style="PASS")
    msg_warn = partialmethod(msg, style="warn")
    msg_WARN = partialmethod(msg, style="WARN")
    msg_fail = partialmethod(msg, style="fail")
    msg_FAIL = partialmethod(msg, style="FAIL")


def main(ctx: CliCtx | None = None):
    """Main entry point that implements the `boldi` CLI."""
    ctx = ctx or CliCtx()
    with ctx:
        ctx.stack.enter_context(error_handler(ctx))

        parser = ArgumentParser(prog="boldi", exit_on_error=False)
        parser.set_defaults(action=partial(parser.print_help, ctx.stderr))
        parser.add_argument("--verbose", "-v", action="store_true", help="enable verbose output")
        parser.add_argument("--chdir", "-C", type=Path, help="change working directory")

        subparsers = parser.add_subparsers(title="action", help="action to run")
        plugins = sorted(boldi.plugins.load("boldi.cli.action"), key=lambda plugin: plugin.name)
        for plugin in plugins:  # type: ignore[type-abstract]
            subparser = subparsers.add_parser(plugin.name)
            subparser.set_defaults(action=partial(subparser.print_help, ctx.stderr))
            _call_with(plugin.impl, ctx=ctx, subparser=subparser)

        try:
            args = vars(parser.parse_args(ctx.argv[1:]))
        except ArgumentError as exc:
            help = parser.format_help().strip()
            if exc.argument_name:
                raise CliUsageException(exc.argument_name + ": " + exc.message, help) from exc
            else:
                raise CliUsageException(exc.message, help) from exc

        ctx.verbose = args.pop("verbose")

        if chdir := args.pop("chdir", None):
            if not chdir.is_dir():
                raise CliUsageException(
                    f"{esc(chdir)} is not a directory",
                    "set [bold]--chdir[/]/[bold]-C[/] to a valid directory or omit it.",
                )
            ctx.chdir(chdir)

        action: Callable[..., None] | None = args.pop("action", None)
        if action and callable(action):
            _call_with(action, **args)
        else:
            parser.print_help(ctx.stderr)


def esc(obj: object) -> str:
    return rich_escape(str(obj))


def _call_with(function: Callable[..., None], **kwargs):
    """Calls `function` with `kwargs`, ignoring excessive kwargs."""
    sig = signature(function)
    param_names = tuple(sig.parameters.keys())
    truncated_kwargs = {k: v for k, v in kwargs.items() if k in param_names}
    bound_args = sig.bind_partial(**truncated_kwargs)
    bound_args.apply_defaults()
    return function(*bound_args.args, **bound_args.kwargs)


@contextmanager
def error_handler(ctx: CliCtx):
    """Context manager that catches all exceptions and converts them to console messages."""
    try:
        yield

    except CliUsageException as exc:
        ctx.msg_FAIL("Error:", exc.args[0])
        if 1 < len(exc.args):
            ctx.msg_warn("[bold]Note:[/]", exc.args[1])  # TODO use Exception notes for Python 3.11+
        if ctx.verbose:
            ctx.console.print(_rich_traceback_from_exception(exc))

        exit(1)

    except Exception as exc:
        ctx.msg_FAIL(f"INTERNAL ERROR: {type(exc).__name__}:", *exc.args)
        ctx.msg_fail("This is a bug, please report it.")
        if ctx.verbose:
            ctx.console.print(_rich_traceback_from_exception(exc))
        else:
            ctx.msg_info("Use [bold]--verbose[/] or [bold]-v[/] for more info.")

        exit(2)


def _rich_traceback_from_exception(exc: Exception) -> Traceback:
    """Get rich Traceback from an exception caught by `error_handler`."""
    tb = exc.__traceback__.tb_next if exc.__traceback__ else None
    return Traceback.from_exception(exc.__class__, exc, tb, extra_lines=2, width=None)
