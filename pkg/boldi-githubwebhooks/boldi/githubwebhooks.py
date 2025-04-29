from __future__ import annotations

from fastapi import FastAPI, Header
from loguru import logger
from pydantic import BaseModel
from starlette.responses import PlainTextResponse

logger.disable(__name__)


class GitHubWebhook(BaseModel):
    gh_hook_id: str = Header(alias="X-GitHub-Hook-ID")
    action: str
    issue: dict
    repository: dict
    sender: dict


class GitHubWebhooksApp(FastAPI):
    def __init__(self, root_path: str = "") -> None:
        super().__init__(root_path=root_path)

        @self.get("/")
        async def get_github_webhook():
            return PlainTextResponse(content="OK")

        @self.post("/")
        async def post_github_webhook():
            return PlainTextResponse(content="OK, noted")

    async def __call__(self, scope, receive, send):
        logger.info(f"{scope=} {receive=} {send=}")
        return await super().__call__(scope, receive, send)
