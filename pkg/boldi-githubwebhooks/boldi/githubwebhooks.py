from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, Header
from loguru import logger
from pydantic import BaseModel
from starlette.responses import PlainTextResponse

logger.disable(__name__)


class GitHubWebhookHeaders(BaseModel):
    # X-GitHub-Delivery: A globally unique identifier (GUID) to identify the event.
    gh_delivery: str = Header(alias="x-github-delivery")
    # X-GitHub-Event: The name of the event that triggered the delivery.
    gh_event: str = Header(alias="x-github-event")
    # X-GitHub-Hook-ID: The unique identifier of the webhook.
    gh_hook_id: str = Header(alias="x-github-hook-id")
    # X-GitHub-Hook-Installation-Target-ID: The unique identifier of the resource where the webhook was created.
    gh_hook_installation_target_id: str = Header(alias="x-github-hook-installation-target-id")
    # X-GitHub-Hook-Installation-Target-Type: The type of resource where the webhook was created.
    gh_hook_installation_target_type: str = Header(alias="x-github-hook-installation-target-type")
    # X-Hub-Signature-256: This header is sent if the webhook is configured with a secret. This is the HMAC hex digest of
    # the request body, and is generated using the SHA-256 hash function and the secret as the HMAC key. For more
    # information, see Validating webhook deliveries.
    hub_signature_256: str | None = Header(alias="x-hub-signature-256", default=None)
    # User-Agent: This header will always have the prefix GitHub-Hookshot/.
    user_agent: str = Header(alias="user-agent")


class PushGitHubWebhook(BaseModel):
    after: str
    base_ref: str | None = None
    before: str
    commits: list[dict]
    compare: str
    created: bool
    deleted: bool
    enterprise: dict | None = None
    forced: bool
    head_commit: dict | None = None
    installation: dict | None = None
    organization: dict | None = None
    pusher: dict
    ref: str
    repository: dict
    sender: dict | None = None


class GitHubWebhooksApp(FastAPI):
    def __init__(self, root_path: str = "") -> None:
        super().__init__(root_path=root_path)

        @self.get("/")
        async def get_github_webhook():
            return PlainTextResponse(content="OK")

        @self.post("/")
        async def post_github_webhook(
            headers: Annotated[GitHubWebhookHeaders, Header()],
            hook: PushGitHubWebhook | dict | None = None,
        ) -> dict:
            return {
                "headers": headers,
                "hook_type": type(hook).__name__,
                "hook": hook,
            }

    async def __call__(self, scope, receive, send):
        logger.info(f"{scope=} {receive=} {send=}")
        return await super().__call__(scope, receive, send)
