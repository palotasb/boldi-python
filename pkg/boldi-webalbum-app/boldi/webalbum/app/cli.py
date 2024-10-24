import os
from argparse import ArgumentParser


def cli_webalbum_app(subparser: ArgumentParser):
    subparser.usage = "run a webalbum-app command"
    webalbum_app_subparsers = subparser.add_subparsers()

    subparser_manage = webalbum_app_subparsers.add_parser("manage")
    subparser_manage.set_defaults(action=cli_webalbum_app_manage)
    subparser_manage.add_argument("args", nargs="*", default=[], help="django manage.py arguments")


def cli_webalbum_app_manage(args):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "boldi.webalbum.app.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(["boldi webalbum-app manage"] + args)
