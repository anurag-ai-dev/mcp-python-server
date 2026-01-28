from fastmcp import FastMCP
from fastmcp.server.providers import FileSystemProvider

from starlette.responses import PlainTextResponse
from starlette.requests import Request
from pathlib import Path

provider = FileSystemProvider(
    root=Path(__file__).parent / "mcp_server",
    reload=True,
)

mcp = FastMCP("weather-mcp-server", providers=[provider])


@mcp.custom_route("/", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("healthy")


app = mcp.http_app()
