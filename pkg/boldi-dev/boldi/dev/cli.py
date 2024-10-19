from argparse import ArgumentParser
from functools import partial

import boldi.cli
import boldi.dev.docs
import boldi.dev.package


class DevCliAction(boldi.cli.CliAction):
    def __init__(self, ctx: boldi.cli.CliCtx, parser: ArgumentParser, subparser: ArgumentParser):
        super().__init__(ctx, parser, subparser)
        subparser.usage = "run a dev command"
        dev_subparsers = subparser.add_subparsers()

        subparser_package = dev_subparsers.add_parser("package")
        subparser_package.set_defaults(action=partial(boldi.dev.package.package, ctx))
        subparser_package.add_argument(
            "--only-include", "-i", nargs="+", default=[], help="only include these packages"
        )

        subparser_docs = dev_subparsers.add_parser("docs")
        subparser_docs.set_defaults(action=partial(boldi.dev.docs.docs, ctx))
