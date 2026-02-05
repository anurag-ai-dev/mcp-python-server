from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.providers import FileSystemProvider
from starlette.requests import Request
from starlette.responses import PlainTextResponse

provider = FileSystemProvider(
    root=Path(__file__).parent / "mcp_server",
    reload=True,
)

mcp = FastMCP("ocr-mcp-server", providers=[provider])


@mcp.custom_route("/", methods=["GET"])
async def health_check(_request: Request) -> PlainTextResponse:
    return PlainTextResponse("healthy")


app = mcp.http_app()
