import asyncio
import mimetypes
import os

import httpx
from fastapi import APIRouter, HTTPException, Request, UploadFile

from logger import get_logger
from ocr import ALLOWED_MIME_TYPES, process_single_url, process_uploaded_file
from schemas import OCRRequest, OCRResponse, OCRStatus, UploadOCRResponse
from settings import settings

logger = get_logger()
router = APIRouter()


@router.get("/")
def health_check():
    """Basic health check"""
    return {"status": "ok", "service": "ocr-service"}


@router.get("/health/ready")
def readiness_check(request: Request):
    """Detailed readiness check"""
    try:
        _pipeline = request.app.state.pipeline
        executor = request.app.state.executor

        import paddle

        device = paddle.device.get_device()

        return {
            "status": "ready",
            "pipeline_initialized": True,
            "executor_running": not executor._shutdown,
            "device": str(device),
        }
    except AttributeError:
        raise HTTPException(
            status_code=503, detail="Service not ready: Pipeline not initialized"
        )


@router.post("/ocr", tags=["OCR"])
async def ocr(request: Request, body: OCRRequest) -> OCRResponse:
    """
    Analyze documents using PaddleOCR-VL.

    - **urls**: List of 1-10 image/PDF URLs (max 10MB each)
    - Supported formats: PNG, JPEG, TIFF, PDF
    """
    try:
        pipeline = request.app.state.pipeline
        executor = request.app.state.executor
    except AttributeError:
        raise HTTPException(status_code=503, detail="OCR pipeline is not initialized")

    async with httpx.AsyncClient() as client:
        tasks = [
            process_single_url(client, url, pipeline, executor) for url in body.urls
        ]
        results = await asyncio.gather(*tasks)

    successful = sum(1 for r in results if r.status == OCRStatus.SUCCESS)
    failed = len(results) - successful

    return OCRResponse(
        results=results,
        total_processed=len(results),
        successful=successful,
        failed=failed,
    )


# THIS IS FOR LOCAL FILES
@router.post("/ocr_upload", tags=["OCR"])
async def ocr_upload(request: Request, file: UploadFile) -> UploadOCRResponse:
    """
    Analyze a directly uploaded document.

    - **file**: Upload an image (PNG, JPEG, TIFF) or PDF (max 10MB)
    """
    try:
        pipeline = request.app.state.pipeline
        executor = request.app.state.executor
    except AttributeError:
        raise HTTPException(status_code=503, detail="OCR pipeline is not initialized")

    filename = file.filename or "uploaded_file"
    content_type = file.content_type or ""

    if content_type and content_type not in ALLOWED_MIME_TYPES:
        return UploadOCRResponse(
            status=OCRStatus.ERROR,
            error=f"Unsupported content type: {content_type}",
            filename=filename,
        )

    content = await file.read()

    if len(content) > settings.MAX_DOWNLOAD_SIZE:
        return UploadOCRResponse(
            status=OCRStatus.ERROR,
            error=f"File too large: {len(content) / 1024 / 1024:.1f}MB (max: 10MB)",
            filename=filename,
        )

    _, ext = os.path.splitext(filename)
    if not ext:
        ext = mimetypes.guess_extension(content_type) or ".png"

    text, error, pages = await process_uploaded_file(
        content, ext, filename, pipeline, executor
    )

    if error:
        return UploadOCRResponse(status=OCRStatus.ERROR, error=error, filename=filename)

    return UploadOCRResponse(
        status=OCRStatus.SUCCESS, text=text, pages=pages, filename=filename
    )
