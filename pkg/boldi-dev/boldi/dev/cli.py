from argparse import ArgumentParser
from typing import Callable, List

import boldi.cli
import boldi.dev.package


class DevCliAction(boldi.cli.CliAction):
    def __init__(self, ctx: boldi.cli.CliCtx, parser: ArgumentParser, subparser: ArgumentParser):
        super().__init__(ctx, parser, subparser)
        subparser.set_defaults(dev_action=self.do_help)
        subparser.usage = "run a dev command"
        dev_subparsers = subparser.add_subparsers()
        subparser_package = dev_subparsers.add_parser("package")
        subparser_package.set_defaults(dev_action=self.do_package)
        subparser_package.add_argument(
            "--only-include", "-i", nargs="+", default=[], help="only include these packages"
        )

    def do_action(self, dev_action: Callable[..., None], **kwargs):
        dev_action(**kwargs)

    def do_help(self):
        self.subparser.print_help(self.ctx.stderr)

    def do_package(self, only_include: List[str]):
        boldi.dev.package.package(self.ctx, only_include)
