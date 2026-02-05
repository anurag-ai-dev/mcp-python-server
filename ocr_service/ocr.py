import asyncio
import mimetypes
import os
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from typing import Any, Generator
from urllib.parse import urlparse

import httpx

from logger import get_logger
from schemas import DownloadError, OCRResult, OCRStatus
from settings import settings

logger = get_logger()

# Allowed MIME types for OCR
ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/tiff",
    "application/pdf",
}


@contextmanager
def temp_file_cleanup(suffix: str) -> Generator[str, None, None]:
    """Context manager for temporary file cleanup"""
    tmp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp_path = tmp_file.name
    tmp_file.close()

    try:
        yield tmp_path
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError as e:
                logger.warning(
                    "Failed to cleanup temp file",
                    extra={"path": tmp_path, "error": str(e)},
                )


@contextmanager
def temp_dir_cleanup() -> Generator[str, None, None]:
    """Context manager for temporary directory cleanup"""
    tmp_dir = tempfile.mkdtemp()

    try:
        yield tmp_dir
    finally:
        if os.path.exists(tmp_dir):
            try:
                shutil.rmtree(tmp_dir)
            except OSError as e:
                logger.warning(
                    "Failed to cleanup temp directory",
                    extra={"path": tmp_dir, "error": str(e)},
                )


async def download_file(client: httpx.AsyncClient, url: str) -> tuple[bytes, str]:
    """Download file from URL and return content with extension."""
    try:
        response = await client.get(
            url, follow_redirects=True, timeout=settings.DOWNLOAD_TIMEOUT
        )
        response.raise_for_status()

        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > settings.MAX_DOWNLOAD_SIZE:
            raise DownloadError(
                f"File too large: {int(content_length) / 1024 / 1024:.1f}MB"
            )

        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        if content_type and content_type not in ALLOWED_MIME_TYPES:
            raise DownloadError(f"Unsupported content type: {content_type}")

        parsed_url = urlparse(url)
        _, ext = os.path.splitext(parsed_url.path)

        if not ext and content_type:
            guessed_ext = mimetypes.guess_extension(content_type)
            if guessed_ext:
                ext = guessed_ext

        if not ext:
            ext = ".png"

        return response.content, ext

    except httpx.TimeoutException as e:
        raise DownloadError(f"Download timeout: {e}")
    except httpx.HTTPStatusError as e:
        raise DownloadError(f"HTTP {e.response.status_code}")
    except httpx.RequestError as e:
        raise DownloadError(f"Request failed: {e}")


async def run_ocr(executor: ThreadPoolExecutor, pipeline: Any, file_path: str) -> Any:
    """Run OCR prediction in thread pool to avoid blocking"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, pipeline.predict, file_path)


def extract_markdown(output: Any, temp_out_dir: str) -> str:
    """Extract markdown content from OCR output"""
    md_content = ""

    if output:
        for res in output:
            if hasattr(res, "save_to_markdown"):
                res.save_to_markdown(save_path=temp_out_dir)
            else:
                logger.warning("Result object missing save_to_markdown method")

    if os.path.exists(temp_out_dir):
        for filename in sorted(os.listdir(temp_out_dir)):
            if filename.endswith(".md"):
                file_path = os.path.join(temp_out_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        md_content += f.read() + "\n\n"
                except Exception as e:
                    logger.error(
                        "Failed to read markdown file",
                        extra={"file": filename, "error": str(e)},
                    )

    return md_content.strip()


async def process_single_url(
    client: httpx.AsyncClient, url: str, pipeline: Any, executor: ThreadPoolExecutor
) -> OCRResult:
    """Process a single URL and return OCR result"""
    try:
        content, ext = await download_file(client, url)

        with temp_file_cleanup(ext) as tmp_file_path:
            with open(tmp_file_path, "wb") as f:
                f.write(content)

            logger.info(
                "Processing file", extra={"url": url, "size_kb": len(content) / 1024}
            )

            output = await run_ocr(executor, pipeline, tmp_file_path)

            with temp_dir_cleanup() as temp_out_dir:
                md_content = extract_markdown(output, temp_out_dir)

            if not md_content:
                return OCRResult(
                    url=url,
                    status=OCRStatus.ERROR,
                    error="No text extracted",
                    error_type="empty_result",
                )

            return OCRResult(
                url=url,
                status=OCRStatus.SUCCESS,
                text=md_content,
                pages=len(output) if output else 0,
            )

    except DownloadError as e:
        logger.warning("Download failed", extra={"url": url, "error": str(e)})
        return OCRResult(
            url=url, status=OCRStatus.ERROR, error=str(e), error_type="download_error"
        )

    except Exception as e:
        logger.error("Processing failed", extra={"url": url, "error": str(e)})
        return OCRResult(
            url=url,
            status=OCRStatus.ERROR,
            error=f"{type(e).__name__}: {str(e)}",
            error_type="processing_error",
        )


async def process_uploaded_file(
    content: bytes, ext: str, filename: str, pipeline: Any, executor: ThreadPoolExecutor
) -> tuple[str | None, str | None, int]:
    """Process uploaded file content and return (text, error, pages)"""
    try:
        with temp_file_cleanup(ext) as tmp_file_path:
            with open(tmp_file_path, "wb") as f:
                f.write(content)

            logger.info(
                "Processing uploaded file",
                extra={"file_name": filename, "size_kb": len(content) / 1024},
            )

            output = await run_ocr(executor, pipeline, tmp_file_path)

            with temp_dir_cleanup() as temp_out_dir:
                md_content = extract_markdown(output, temp_out_dir)

            if not md_content:
                return None, "No text extracted from document", 0

            return md_content, None, len(output) if output else 0

    except Exception as e:
        logger.error(
            "Upload processing failed", extra={"file_name": filename, "error": str(e)}
        )
        return None, f"{type(e).__name__}: {str(e)}", 0
