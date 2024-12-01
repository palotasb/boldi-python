from argparse import ArgumentParser
from functools import partial
from importlib import import_module
from importlib.resources import open_text

from boldi.cli import CliCtx

YEAR = 2024


def cli_aoc(ctx: CliCtx, subparser: ArgumentParser):
    subparser.add_argument("day")
    subparser.set_defaults(action=partial(aoc_run, ctx))


def aoc_run(ctx: CliCtx, day: int):
    name = f"y{YEAR}d{day}"
    try:
        module = import_module(f".{name}", __name__)
        with open_text(__name__, f"res/{name}.in.txt") as input:
            module.main(ctx, input)
    except ImportError:
        ctx.msg_fail(f"day {day} not implemented")
        exit(1)
