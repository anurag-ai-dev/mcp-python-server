# MCP Weather Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server built with Python and `uv`.
This server exposes weather-related tools powered by the National Weather Service (NWS) API.

## 🛠️ Tools

1.  **`get_alerts(state: str)`**:
    - Fetches active weather alerts for a specific US state.
    - Example: `get_alerts("CA")`
2.  **`get_forecast(latitude: str, longitude: str)`**:
    - Retrieves detailed weather forecasts for a geolocation.
    - Example: `get_forecast("37.7749", "-122.4194")`

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- `uv` (for package management):
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- `npm` (optional, for Inspector)

### Installation

Clone the repository and install dependencies:

```bash
make install
```

### Running the Server

Start the MCP server:

```bash
make dev
```

(This runs `uv run python main.py` using stdio transport).

### Inspecting Tools

Use the MCP Inspector to interactively test the tools:

```bash
make inspector
```

This command starts the inspector UI, where you can list tools and simulate client requests.

### Development

- **Format code**: `make format` (uses `ruff`)
- **Type check**: `make mypy`

## 📂 Project Structure

```
├── main.py              # Server entry point
├── mcp_server/
│   ├── tools.py         # Tool logic (Visual fetching/formatting)
│   └── helpers.py       # API helpers
├── settings.py          # Configuration (Pydantic)
├── Makefile             # Command shortcuts
└── pyproject.toml       # Dependencies
```

## 🔒 Security

- Uses `pydantic-settings` for configuration management.
- Tools are read-only and access public APIs.
