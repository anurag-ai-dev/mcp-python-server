from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response

from logger import RequestContextVar, get_logger, request_ctx_var
from routes import router

logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the PaddleOCR pipeline and thread pool at startup."""
    try:
        logger.info("Initializing PaddleOCR-VL pipeline...")
        import paddle
        from paddleocr import PaddleOCRVL

        device = paddle.device.get_device()
        logger.info("PaddlePaddle device", extra={"device": device})

        if "gpu" not in device and "cuda" not in device:
            logger.warning("GPU not detected! Inference will be slow.")

        pipeline = PaddleOCRVL(
            use_doc_orientation_classify=True, use_layout_detection=True
        )
        app.state.pipeline = pipeline

        # Use max_workers=1 to serialize GPU operations and prevent OOM
        app.state.executor = ThreadPoolExecutor(max_workers=1)

        logger.info("PaddleOCR-VL pipeline initialized successfully")

    except Exception as e:
        logger.error(
            "Failed to initialize PaddleOCR-VL pipeline", extra={"error": str(e)}
        )
        raise RuntimeError(f"OCR Pipeline initialization failed: {e}")

    yield

    if hasattr(app.state, "executor"):
        app.state.executor.shutdown(wait=True)
        logger.info("Thread pool executor shut down")

    if hasattr(app.state, "pipeline"):
        del app.state.pipeline

    logger.info("OCR service shut down")


app = FastAPI(
    title="OCR Service",
    description="Microservice for PaddleOCR-VL with async processing",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def logging_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Add request ID and logging context"""
    request_id = str(uuid4())
    request_path = f"{request.method} {request.url.path}"

    token = request_ctx_var.set(
        RequestContextVar(request_id=request_id, request_path=request_path)
    )

    logger.info("Request received")

    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        request_ctx_var.reset(token)


app.include_router(router)
