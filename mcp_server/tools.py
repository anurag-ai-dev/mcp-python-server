import base64
import os

import httpx
from fastmcp.tools import tool

from settings import settings
from utils.logger import get_logger

logger = get_logger()


@tool(
    name="ocr_local_glm",
    description=(
        "Analyze a local image using the local GLM-OCR model via Ollama. "
        "Best for privacy and cost-efficiency. "
        "Requires 'glm-ocr' model in Ollama."
    ),
)
async def ocr_local_glm(file_path: str) -> str:
    """
    Use local GLM-OCR model via Ollama to analyze an image.

    Args:
        file_path: Absolute path to the local image file (jpg, png)

    Returns:
        Extracted text and structured data in Markdown format
    """
    if not os.path.exists(file_path):
        return f"Error: File not found: {file_path}"

    if not os.path.isfile(file_path):
        return f"Error: Not a file: {file_path}"

    # Basic file type check
    valid_exts = {".jpg", ".jpeg", ".png"}
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in valid_exts:
        return (
            f"Error: Unsupported file type '{ext}'. Supported: {', '.join(valid_exts)}"
        )

    try:
        with open(file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

        url = settings.OLLAMA_URL
        payload = {
            "model": "glm-ocr:latest",
            "messages": [
                {
                    "role": "user",
                    "content": "Extract all text and data from this image exactly as it appears. Format tables as markdown.",
                    "images": [encoded_string],
                }
            ],
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=settings.TIMEOUT) as client:
            logger.info("Sending request to local GLM-OCR", extra={"file": file_path})
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

            content = result.get("message", {}).get("content", "")
            if content:
                logger.info("Local OCR completed", extra={"file": file_path})
                return content
            else:
                return "Error: No content returned from local model"

    except httpx.ConnectError:
        return f"Error: Could not connect to Ollama at {settings.OLLAMA_URL}. Is it running?"
    except httpx.TimeoutException:
        return "Error: Local OCR timed out (model might be slow or loading)"
    except Exception as e:
        logger.exception("Unexpected local OCR error")
        return f"Error: {str(e)}"
