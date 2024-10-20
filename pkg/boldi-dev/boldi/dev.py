from argparse import ArgumentParser
from collections.abc import Callable
from functools import partial
from itertools import chain
from pathlib import Path

from boldi.cli import CliCtx


def cli_dev(ctx: CliCtx, subparser: ArgumentParser):
    subparser.usage = "run a dev command"
    dev_subparsers = subparser.add_subparsers()

    subparser_package = dev_subparsers.add_parser("package")
    subparser_package.set_defaults(action=partial(cli_dev_package, ctx))
    subparser_package.add_argument("--only-include", "-i", nargs="+", default=[], help="only include these packages")

    subparser_docs = dev_subparsers.add_parser("docs")
    subparser_docs.set_defaults(action=partial(cli_dev_docs, ctx))


def first_parent_where(dir: Path, predicate: Callable[[Path], bool]) -> Path | None:
    return next(filter(predicate, chain([dir], dir.parents)), None)


def cli_dev_docs(ctx: CliCtx):
    if root := first_parent_where(ctx.cwd, lambda parent: (parent / "mkdocs.yml").is_file()):
        ctx.run_py("-m mkdocs build", cwd=root)


def cli_dev_package(ctx: CliCtx, only_include: list[str]):
    if root := first_parent_where(ctx.cwd, lambda parent: (parent / ".git").is_dir()):
        only_include_set = set(only_include)
        for pkg in sorted((root / "pkg").iterdir()):
            should_include = not only_include_set or pkg.name in only_include_set
            is_package = pkg.is_dir() and (pkg / "pyproject.toml").is_file()
            if should_include and is_package:
                ctx.run_py("-m build --no-isolation --sdist --wheel", ["--outdir", root / "dist"], cwd=pkg)
