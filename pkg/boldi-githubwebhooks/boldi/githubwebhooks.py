from loguru import logger
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response

# logger.disable(__name__)


class GitHubWebhooksApp(Starlette):
    def __init__(self) -> None:
        super().__init__()
        self.add_route("/", self.post_github_webhook, methods=["GET", "POST"])

    async def post_github_webhook(self, request: Request) -> Response:
        logger.info("{} {} {}", request.method, request.url, vars(request))
        content = await request.body()
        logger.info("content: {}", content)
        return Response(content=content, status_code=200, media_type=request.headers.get("Content-Type"))
