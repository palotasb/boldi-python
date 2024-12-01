import os
from argparse import ArgumentParser


def cli_api(subparser: ArgumentParser):
    subparser.usage = "run an api command"
    webalbum_app_subparsers = subparser.add_subparsers()

    subparser_manage = webalbum_app_subparsers.add_parser("manage")
    subparser_manage.set_defaults(action=cli_api_manage)
    subparser_manage.add_argument("args", nargs="*", default=[], help="django manage.py arguments")


def cli_api_manage(args):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "boldi.api.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(["boldi api manage"] + args)
