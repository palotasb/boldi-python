from abc import ABC, abstractmethod
from argparse import ArgumentParser
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from rich.console import Console

import boldi
import boldi.plugins
from boldi.ctx import Ctx


class _CliCtxDefaultConsole(Console):
    pass


@dataclass
class CliCtx(Ctx):
    console: Console = field(default_factory=_CliCtxDefaultConsole)

    def __post_init__(self):
        if isinstance(self.console, _CliCtxDefaultConsole):
            self.console = Console(file=self.stderr, highlight=False)


@dataclass
class Action:
    subparser_kwargs: dict[str, Any]
    argument_parser: Callable[[ArgumentParser], None]
    action_fn: Callable[..., None]


class CliAction(ABC):
    ctx: CliCtx
    parser: ArgumentParser
    subparser: ArgumentParser

    def __init__(self, ctx: CliCtx, parser: ArgumentParser, subparser: ArgumentParser):
        self.ctx = ctx
        self.parser = parser
        self.subparser = subparser

    @abstractmethod
    def do_action(self, *args, **kwargs):
        raise NotImplementedError


class HelpCliAction(CliAction):
    help = "show this help message and exit"

    def do_action(self):
        self.parser.print_help()


def main(ctx: Optional[CliCtx] = None):
    ctx = ctx or CliCtx()
    with ctx:
        ctx.stack.enter_context(error_handler(ctx))
        parser = ArgumentParser(prog=boldi.__name__)
        subparsers = parser.add_subparsers(title="action", help="action to run")
        for plugin in boldi.plugins.load("cli.action", subclass=CliAction):
            cli_action_cls = plugin.obj
            subparser = subparsers.add_parser(plugin.name)
            cli_action = cli_action_cls(ctx, parser, subparser)
            subparser.set_defaults(action=cli_action.do_action)

        args = vars(parser.parse_args(ctx.argv[1:]))
        action: Optional[Callable[..., None]] = args.pop("action", None)
        if action:
            action(**args)
        else:
            parser.print_help()


@contextmanager
def error_handler(ctx: CliCtx):
    try:
        yield
    except Exception as exc:
        ctx.console.print(f"[bold red]INTERNAL ERROR[/]: {type(exc).__name__}:", *exc.args)
