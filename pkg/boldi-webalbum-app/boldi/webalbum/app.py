from argparse import ArgumentParser
from functools import partial

from fastapi import FastAPI

from boldi.cli import CliCtx


def app():
    fastapi_app = FastAPI(title="boldi webalbum app")

    @fastapi_app.get("/")
    def index():
        return {"message": "Hello, World!"}

    return fastapi_app


def cli_webalbum_app(ctx: CliCtx, subparser: ArgumentParser):
    subparser.usage = "run a webalbum-app command"
    webalbum_app_subparsers = subparser.add_subparsers()

    subparser_run = webalbum_app_subparsers.add_parser("run")
    subparser_run.set_defaults(action=partial(cli_webalbum_app_run, ctx))
    subparser_run.add_argument("args", nargs="*", default=[], help="uvicorn arguments")


def cli_webalbum_app_run(ctx: CliCtx, args: list[str]):
    ctx.run("uvicorn --factory", args, f"{__name__}:app")
