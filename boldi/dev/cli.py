from argparse import ArgumentParser
from typing import Callable

import boldi.cli

from .package import package


class DevCliAction(boldi.cli.CliAction):
    def __init__(self, ctx: boldi.cli.CliCtx, parser: ArgumentParser, subparser: ArgumentParser):
        super().__init__(ctx, parser, subparser)
        subparser.set_defaults(dev_action=self.do_help)
        subparser.usage = "run a dev command"
        dev_subparsers = subparser.add_subparsers()
        dsp_package = dev_subparsers.add_parser("package")
        dsp_package.set_defaults(dev_action=self.do_package)

    def do_action(self, dev_action: Callable[..., None], **kwargs):
        dev_action(**kwargs)

    def do_help(self):
        self.subparser.print_help(self.ctx.stderr)

    def do_package(self):
        package(self.ctx)
