import os
from argparse import REMAINDER, ArgumentParser

import boldi.cli


class WebalbumAppCliAction(boldi.cli.CliAction):
    def __init__(self, ctx: boldi.cli.CliCtx, parser: ArgumentParser, subparser: ArgumentParser):
        super().__init__(ctx, parser, subparser)
        subparser.set_defaults(action=lambda: subparser.print_help(ctx.stderr))
        subparser.usage = "run a webalbum-app command"
        webalbum_app_subparsers = subparser.add_subparsers()

        subparser_manage = webalbum_app_subparsers.add_parser("manage")
        subparser_manage.set_defaults(action=self.action_manage)
        subparser_manage.add_argument("args", nargs=REMAINDER, default=[], help="django manage.py arguments")

    def action_manage(self, args):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "boldi.webalbum.app.settings")
        from django.core.management import execute_from_command_line

        execute_from_command_line(["boldi webalbum-app manage"] + args)
