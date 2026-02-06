import asyncio
import base64
import os

import httpx
from fastmcp.tools import tool

from settings import settings
from utils.logger import get_logger

logger = get_logger()


@tool(
    name="ocr_document",
    description=(
        "Analyze complex documents with tables, charts, and multiple columns. "
        "Best for Japanese/English layouts, invoices, and research papers. "
        "Supports PNG, JPEG, TIFF, and PDF formats (max 10MB)."
    ),
)
async def ocr_document(file_url: str) -> str:
    """
    Uses a remote PaddleOCR service to analyze complex documents.
    Returns the content in Markdown format with layout preserved.

    Args:
        file_url: URL to the image or PDF file (must be publicly accessible)

    Returns:
        Markdown-formatted text extracted from the document
    """
    retry_attempts = 3
    timeout = 60

    if not file_url.startswith(("http://", "https://")):
        logger.error("Invalid URL scheme", extra={"url": file_url})
        return f"Error: Invalid URL scheme. Provided: {file_url}"

    for attempt in range(retry_attempts):
        try:
            payload = {"urls": [file_url]}

            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.info(
                    "Sending OCR request",
                    extra={"url": file_url, "attempt": attempt + 1},
                )

                response = await client.post(
                    settings.OCR_SERVICE_URL, json=payload, timeout=timeout
                )
                response.raise_for_status()
                result = response.json()

                if "results" in result and result["results"]:
                    markdown_outputs = []
                    errors = []

                    for res in result["results"]:
                        if res.get("status") == "success" and res.get("text"):
                            markdown_outputs.append(res["text"])
                        elif "text" in res and res["text"]:
                            markdown_outputs.append(res["text"])
                        elif res.get("error"):
                            errors.append(res["error"])

                    if markdown_outputs:
                        full_text = "\n\n---\n\n".join(markdown_outputs)
                        logger.info("OCR completed", extra={"url": file_url})
                        return full_text

                    if errors:
                        logger.warning(
                            "OCR errors", extra={"url": file_url, "errors": errors}
                        )
                        return f"OCR Failed: {'; '.join(errors)}"

                logger.warning("No text extracted", extra={"url": file_url})
                return "No text extracted from document."

        except httpx.TimeoutException:
            logger.warning(
                "OCR timeout", extra={"attempt": attempt + 1, "url": file_url}
            )
            if attempt < retry_attempts - 1:
                await asyncio.sleep(2**attempt)
                continue
            return f"OCR Failed: Timeout after {retry_attempts} attempts"

        except httpx.HTTPStatusError as e:
            logger.error(
                "OCR HTTP error",
                extra={"status_code": e.response.status_code, "url": file_url},
            )
            return f"OCR Failed: HTTP {e.response.status_code}"

        except httpx.RequestError as e:
            logger.error(
                "OCR connection failed", extra={"error": str(e), "url": file_url}
            )
            if attempt < retry_attempts - 1:
                await asyncio.sleep(2**attempt)
                continue
            return f"OCR Failed: Connection error - {type(e).__name__}"

        except Exception as e:
            logger.exception("Unexpected OCR error", extra={"url": file_url})
            return f"OCR Failed: {type(e).__name__}: {str(e)}"

    return f"OCR Failed: Max retries ({retry_attempts}) exceeded"


@tool(
    name="ocr_batch_documents",
    description=(
        "Analyze multiple documents in a single batch request. "
        "More efficient than analyzing documents one at a time. "
        "Maximum 10 URLs per batch."
    ),
)
async def ocr_batch_documents(file_urls: list[str]) -> str:
    """
    Analyze multiple documents in parallel using the OCR service.

    Args:
        file_urls: List of URLs to process (max 10)

    Returns:
        Summary of results with extracted text for successful documents
    """
    timeout = 120

    if not file_urls:
        return "Error: No URLs provided"

    if len(file_urls) > 10:
        return f"Error: Maximum 10 URLs allowed (provided: {len(file_urls)})"

    invalid_urls = [
        url for url in file_urls if not url.startswith(("http://", "https://"))
    ]
    if invalid_urls:
        return f"Error: Invalid URL schemes: {', '.join(invalid_urls[:3])}"

    try:
        payload = {"urls": file_urls}

        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info(
                "Sending batch OCR request", extra={"url_count": len(file_urls)}
            )

            response = await client.post(
                settings.OCR_SERVICE_URL, json=payload, timeout=timeout
            )
            response.raise_for_status()
            result = response.json()

            if "results" not in result:
                return "Error: Unexpected response format"

            successful = result.get("successful", 0)
            total = result.get("total_processed", len(file_urls))

            output_parts = [f"Batch OCR: {successful}/{total} successful\n"]

            for i, res in enumerate(result["results"], 1):
                url = res.get(
                    "url", file_urls[i - 1] if i <= len(file_urls) else "unknown"
                )
                status = res.get("status", "success" if res.get("text") else "error")

                output_parts.append(f"\n### Document {i}: {url}\n")

                if (status == "success" or "text" in res) and res.get("text"):
                    output_parts.append(f"{res['text']}\n")
                elif res.get("error"):
                    output_parts.append(f"Error: {res['error']}\n")

            logger.info(
                "Batch OCR completed", extra={"successful": successful, "total": total}
            )
            return "".join(output_parts)

    except httpx.TimeoutException:
        logger.error("Batch OCR timeout", extra={"timeout": timeout})
        return f"Batch OCR Failed: Timeout after {timeout}s"

    except httpx.HTTPStatusError as e:
        logger.error(
            "Batch OCR HTTP error", extra={"status_code": e.response.status_code}
        )
        return f"Batch OCR Failed: HTTP {e.response.status_code}"

    except httpx.RequestError as e:
        logger.error("Batch OCR connection failed", extra={"error": str(e)})
        return "Batch OCR Failed: Connection error"

    except Exception as e:
        logger.exception("Unexpected batch OCR error")
        return f"Batch OCR Failed: {type(e).__name__}: {str(e)}"


# THIS IS FOR LOCAL FILES
@tool(
    name="ocr_uploaded_document",
    description=(
        "Analyze a local file by uploading it directly to the OCR service. "
        "Use this when you have a file path instead of a URL. "
        "Supports PNG, JPEG, TIFF, and PDF formats (max 10MB)."
    ),
)
async def ocr_uploaded_document(file_path: str) -> str:
    """
    Upload a local file to the OCR service for analysis.

    Args:
        file_path: Path to the local image or PDF file

    Returns:
        Markdown-formatted text extracted from the document
    """
    import os

    if not os.path.exists(file_path):
        return f"Error: File not found: {file_path}"

    if not os.path.isfile(file_path):
        return f"Error: Not a file: {file_path}"

    file_size = os.path.getsize(file_path)
    max_size = 10 * 1024 * 1024
    if file_size > max_size:
        return f"Error: File too large: {file_size / 1024 / 1024:.1f}MB (max: 10MB)"

    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()

    content_type_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".tiff": "image/tiff",
        ".pdf": "application/pdf",
    }

    content_type = content_type_map.get(ext)
    if not content_type:
        return f"Error: Unsupported file type: {ext}"

    timeout = 120

    try:
        upload_url = settings.OCR_SERVICE_URL.replace(
            "/predict/ocr_system", "/predict/ocr_upload"
        )

        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info("Uploading file for OCR", extra={"file_path": file_path})

            with open(file_path, "rb") as f:
                files = {"file": (filename, f, content_type)}
                response = await client.post(upload_url, files=files, timeout=timeout)

            response.raise_for_status()
            result = response.json()

            if result.get("status") == "success" and result.get("text"):
                logger.info("File OCR completed", extra={"file_path": file_path})
                return result["text"]

            if result.get("error"):
                return f"OCR Failed: {result['error']}"

            return "No text extracted from document."

    except httpx.TimeoutException:
        logger.error("OCR upload timeout")
        return f"OCR Failed: Timeout after {timeout}s"

    except httpx.HTTPStatusError as e:
        logger.error(
            "OCR upload HTTP error", extra={"status_code": e.response.status_code}
        )
        return f"OCR Failed: HTTP {e.response.status_code}"

    except httpx.RequestError as e:
        logger.error("OCR upload connection failed", extra={"error": str(e)})
        return "OCR Failed: Connection error. Is OCR service running?"

    except Exception as e:
        logger.exception("Unexpected OCR upload error")
        return f"OCR Failed: {type(e).__name__}: {str(e)}"


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
        # 1. Read and encode image
        with open(file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

        # 2. Construct Ollama request
        url = "http://localhost:11434/api/chat"
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

        # 3. Send request
        timeout = 180  # Local inference can be slow
        async with httpx.AsyncClient(timeout=timeout) as client:
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
        return "Error: Could not connect to Ollama at http://localhost:11434. Is it running?"
    except httpx.TimeoutException:
        return "Error: Local OCR timed out (model might be slow or loading)"
    except Exception as e:
        logger.exception("Unexpected local OCR error")
        return f"Error: {str(e)}"
