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
    # The SHA of the most recent commit on `ref` after the push.
    after: str
    # ?
    base_ref: str | None = None
    # The SHA of the most recent commit on `ref` before the push.
    before: str
    # An array of commit objects describing the pushed commits. (Pushed commits are all commits that are included in the compare between the before commit and the after commit.) The array includes a maximum of 2048 commits. If necessary, you can use the Commits API to fetch additional commits.
    commits: list[Commit]
    # URL that shows the changes in this ref update, from the before commit to the after commit. For a newly created ref that is directly based on the default branch, this is the comparison between the head of the default branch and the after commit. Otherwise, this shows all commits until the after commit.
    compare: str
    # Whether this push created the `ref`.
    created: bool
    # Whether this push deleted the `ref`.
    deleted: bool
    # An enterprise on GitHub. Webhook payloads contain the enterprise property when the webhook is configured on an enterprise account or an organization that's part of an enterprise account. For more information, see "About enterprise accounts."
    enterprise: dict | None = None
    # Whether this push was a force push of the `ref`.
    forced: bool
    # TODO
    head_commit: Commit | None  # may be None, but is required
    # The GitHub App installation. Webhook payloads contain the installation property when the event is configured for and sent to a GitHub App. For more information, see "Using webhooks with GitHub Apps."
    installation: dict | None = None
    # A GitHub organization. Webhook payloads contain the organization property when the webhook is configured for an organization, or when the event occurs from activity in a repository owned by an organization.
    organization: dict | None = None
    # Metaproperties for Git author/committer information.
    pusher: User
    # The full git ref that was pushed. Example: `refs/heads/main` or `refs/tags/v3.14.1`.
    ref: str
    # TODO A git repository ???
    repository: dict
    # A GitHub user.
    sender: dict | None = None


class Commit(BaseModel):
    # An array of files added in the commit. A maximum of 3000 changed files will be reported per commit.
    added: list[str]
    # Metaproperties for Git author information.
    author: User
    # Metaproperties for Git committer information.
    committer: User
    # Whether this commit is distinct from any that have been pushed before.
    distinct: bool
    # ID
    id: str
    # The commit message.
    message: str
    # An array of files modified by the commit. A maximum of 3000 changed files will be reported per commit.
    modified: list[str]
    # An array of files removed in the commit. A maximum of 3000 changed files will be reported per commit.
    removed: list[str]
    # The ISO 8601 timestamp of the commit.
    timestamp: str  # TODO type as datetime
    # Tree ID
    tree_id: str
    # URL that points to the commit API resource.
    url: str


class User(BaseModel):
    """Metaproperties for Git author/committer information."""

    date: str | None = None
    email: str | None  # may be None, but is required
    name: str
    username: str | None = None


class GitHubWebhooksApp(FastAPI):
    def __init__(self, root_path: str = "") -> None:
        super().__init__(root_path=root_path)

        @self.get("/")
        async def get_github_webhook():
            return PlainTextResponse(content="OK")

        @self.post("/")
        async def post_github_webhook(
            headers: Annotated[GitHubWebhookHeaders, Header()],
            hook: PushGitHubWebhook | dict,
        ) -> dict:
            match hook:
                case push if isinstance(push, PushGitHubWebhook):
                    return await handle_post_hook(headers, push)
                case hook if isinstance(hook, dict):
                    return {"headers": headers, "hook": hook}
                case _:
                    assert False, "unreachable, otherwise internal error"

        async def handle_post_hook(headers: GitHubWebhookHeaders, push: PushGitHubWebhook) -> dict:
            return {
                "headers": headers,
                "push": push.model_dump(mode="json"),
            }

    async def __call__(self, scope, receive, send):
        logger.info(f"{scope=} {receive=} {send=}")
        return await super().__call__(scope, receive, send)
