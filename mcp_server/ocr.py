import base64
import logging
import os

import httpx
from fastmcp.tools import tool

from settings import settings


@tool(
    name="analyze_complex_document",
    description="Analyze complex documents (tables, charts, multiple columns).",
)
async def analyze_complex_document(image_path: str) -> str:
    """
    Uses a remote PaddleOCR service to analyze complex documents.
    Best for Japanese/English layouts, invoices, and research papers.
    Returns the content in Markdown format (or raw text).

    Args:
        image_path: Local path to the image file.
    """
    if not os.path.exists(image_path):
        return f"Error: File not found at {image_path}"

    try:
        # Read the image file
        with open(image_path, "rb") as f:
            image_data = f.read()

        # Encode to base64 for reliable transmission over JSON or use multipart/form-data
        # PaddleHub/Serving often accepts images as base64 string in JSON
        image_b64 = base64.b64encode(image_data).decode("utf-8")

        payload = {"images": [image_b64]}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.OCR_API_URL, json=payload, timeout=60.0
            )
            response.raise_for_status()
            result = response.json()

            # Helper to recursively extract text from unknown JSON structure
            # (Adjust based on actual API response format)
            def extract_text(data):
                texts = []
                if isinstance(data, dict):
                    for key, value in data.items():
                        if key == "text" and isinstance(value, str):
                            texts.append(value)
                        else:
                            texts.extend(extract_text(value))
                elif isinstance(data, list):
                    for item in data:
                        texts.extend(extract_text(item))
                return texts

            # Assuming standard Paddle output which usually contains 'results' -> list of 'data' -> 'text'
            # Or formatted markdown if the service is the specific MCP one.
            # For now, let's just dump the JSON or extract text generically.

            if "results" in result:
                # Basic text extraction
                full_text = "\n".join(extract_text(result["results"]))
                return full_text if full_text else str(result)

            return str(result)

    except httpx.RequestError as e:
        logging.error("OCR API Connection Failed:", extra={"error": e})
        return f"OCR Analysis Failed: Could not connect to OCR service at {settings.OCR_API_URL}. Is it running?"
    except Exception as e:
        logging.error("OCR Analysis Failed:", extra={"exception": e})
        return f"OCR Analysis Failed: {str(e)}"
