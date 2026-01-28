from fastmcp import FastMCP
from fastmcp.server.providers import FileSystemProvider

from pathlib import Path

provider = FileSystemProvider(
    root=Path(__file__).parent / "mcp_server",
    reload=True,
)

mcp = FastMCP("weather-mcp-server", providers=[provider])

if __name__ == "__main__":
    mcp.run()
