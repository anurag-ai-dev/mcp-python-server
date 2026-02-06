# OCR MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server built with Python.
This server exposes OCR (Optical Character Recognition) tools powered by a local **GLM-OCR** model running via **Ollama**.

## 🛠️ Capabilities

The server provides a tool to analyze documents using the local GLM-OCR model.

1.  **`ocr_local_glm(file_path: str)`**:
    - Analyzes a local image file (JPG, PNG) using the GLM-OCR model.
    - Extracts text and structured data in Markdown format.
    - **Note:** Requires Ollama to be running with the `glm-ocr` model available.
    - Example: `ocr_local_glm("/home/user/docs/scan.png")`

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- `uv` (for package management):
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Ollama**: [Download and install Ollama](https://ollama.com/).
- **GLM-OCR Model**:
  Pull the required model:
  ```bash
  ollama pull glm-ocr
  ```
- `npm` (optional, for Inspector)

### Installation

1. Clone the repository.
2. Install dependencies for the MCP server:
   ```bash
   make install
   ```

### Running the Server

Running this system requires **Ollama** and the **MCP Server**.

1.  **Ensure Ollama is running**:
    Make sure the Ollama service is active. You can often check this by running `ollama list` or ensuring the background service is started.

2.  **Start the MCP Server**:
    ```bash
    make mcp
    ```
    _This runs on port 8001._

### Inspecting Tools

Use the MCP Inspector to interactively test the tools:

```bash
make inspect
```

This command starts the inspector UI, where you can list tools and simulate client requests.

### Development

- **Format code**: `make format` (uses `ruff`)
- **Type check**: `make mypy`

## 📂 Project Structure

```
├── main.py              # MCP Server entry point
├── mcp_server/          # MCP Server Implementation
│   ├── tools.py         # Tool logic (GLM-OCR bridge)
├── settings.py          # Configuration
├── Makefile             # Command shortcuts
└── pyproject.toml       # MCP Server Dependencies
```

## 🔒 Security

- The OCR process runs entirely locally via Ollama; no image data is sent to external cloud providers.
- The tool validates that the input path exists and is a file.
