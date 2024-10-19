from argparse import ArgumentParser
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import partial

from rich.console import Console

import boldi
import boldi.plugins
from boldi.ctx import Ctx


class _CliCtxDefaultConsole(Console):
    """Implementation detail used to set a default value for [boldi.cli.CliCtx.console][]."""

    pass


@dataclass
class CliCtx(Ctx):
    """Extends [`Ctx`][boldi.ctx.Ctx] with a console feature for rich CLI output."""

    console: Console = field(default_factory=_CliCtxDefaultConsole)
    """A rich console that outputs to `self.stderr` by default."""

    def __post_init__(self):
        if isinstance(self.console, _CliCtxDefaultConsole):
            self.console = Console(file=self.stderr, highlight=False)


@dataclass
class CliAction:
    """
    Base class for implementing a `boldi` CLI subcommand.
    """

    ctx: CliCtx
    """Context provided for convenience."""

    parser: ArgumentParser
    """The root [`argparse.ArgumentParser`][] for the `boldi` CLI."""

    subparser: ArgumentParser
    """The subcommand [`argparse.ArgumentParser`][] for the `boldi` CLI subcommand implemented by this class."""


def main(ctx: CliCtx | None = None):
    """Main entry point that implements the `boldi` CLI."""
    ctx = ctx or CliCtx()
    with ctx:
        ctx.stack.enter_context(error_handler(ctx))
        parser = ArgumentParser(prog="boldi")
        parser.set_defaults(action=partial(parser.print_help, ctx.stderr))
        subparsers = parser.add_subparsers(title="action", help="action to run")
        for plugin in boldi.plugins.load("boldi.cli.action", cls=CliAction):  # type: ignore[type-abstract]
            subparser = subparsers.add_parser(plugin.name)
            subparser.set_defaults(action=partial(subparser.print_help, ctx.stderr))
            plugin.cls(ctx, parser, subparser)

        args = vars(parser.parse_args(ctx.argv[1:]))
        action: Callable[..., None] | None = args.pop("action", None)
        if action:
            action(**args)
        else:
            parser.print_help(ctx.stderr)


@contextmanager
def error_handler(ctx: CliCtx):
    """Context manager that catches all exceptions and converts them to console messages."""
    try:
        yield
    except Exception as exc:
        ctx.console.print(f"[bold red]INTERNAL ERROR[/]: {type(exc).__name__}:", *exc.args)
