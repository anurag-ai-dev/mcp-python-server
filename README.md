# OCR MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server built with Python.
This server exposes OCR (Optical Character Recognition) tools powered by a local PaddleOCR service, capable of extracting text and layout from complex images and PDFs, including Japanese text.

## 🛠️ Capabilities

The server provides tools to analyze documents via a dedicated OCR backend service.

1.  **`ocr_document(file_url: str)`**:
    - Analyzes a single document through its URL (Image/PDF).
    - Preserves layout and returns Markdown.
    - Example: `ocr_document("https://example.com/invoice.pdf")`

2.  **`ocr_batch_documents(file_urls: list[str])`**:
    - Analyzes multiple documents through their URLs in parallel.
    - efficient for processing multiple files (max 10).
    - Example: `ocr_batch_documents(["https://example.com/a.jpg", "https://example.com/b.pdf"])`

3.  **`ocr_uploaded_document(file_path: str)`**:
    - Analyzes a local file by uploading it to the OCR service.
    - **Note:** Requires the file to be accessible on the local filesystem.
    - Example: `ocr_uploaded_document("/home/user/docs/scan.png")`

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- `uv` (for package management):
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- `npm` (optional, for Inspector)
- CUDA-compatible GPU (Recommended for faster OCR performance)

### Installation

1. Clone the repository.
2. Install dependencies for the MCP server:
   ```bash
   make install
   ```

### Running the Server

Running this system requires two components: the **OCR Backend Service** and the **MCP Server**.

1.  **Start the OCR Service** (controls the PaddleOCR model):

    ```bash
    make ocr
    ```

    _This runs on port 8866._

2.  **Start the MCP Server** (in a new terminal):
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
│   ├── tools.py         # Tool logic (OCR bridge)
├── ocr_service/         # OCR Backend Service (FastAPI + PaddleOCR)
│   ├── main.py          # FastAPI app
│   └── ocr.py           # PaddleOCR logic
├── settings.py          # Configuration
├── Makefile             # Command shortcuts
└── pyproject.toml       # MCP Server Dependencies
```

## 🔒 Security

- The OCR service runs locally; no data is sent to external cloud providers for OCR.
- Tools validate URL schemes and file paths.
