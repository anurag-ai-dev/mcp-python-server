from enum import Enum

from pydantic import BaseModel, Field, field_validator

from settings import settings


# Custom Exceptions
class OCRError(Exception):
    """Base OCR error"""

    pass


class DownloadError(OCRError):
    """File download failed"""

    pass


class ProcessingError(OCRError):
    """OCR processing failed"""

    pass


class ValidationError(OCRError):
    """Input validation failed"""

    pass


# Enums
class OCRStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"


# Request/Response Models
class OCRRequest(BaseModel):
    urls: list[str] = Field(
        ...,
        min_length=1,
        max_length=settings.MAX_URLS_PER_REQUEST,
        description="List of image/PDF URLs to process",
    )

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, v: list[str]) -> list[str]:
        for url in v:
            if not url.startswith(("http://", "https://")):
                raise ValueError(f"URL must start with http:// or https://: {url}")
        return v

    model_config = {
        "json_schema_extra": {"example": {"urls": ["https://example.com/invoice.pdf"]}}
    }


class OCRResult(BaseModel):
    url: str
    status: OCRStatus
    text: str | None = None
    error: str | None = None
    error_type: str | None = None
    pages: int | None = None


class OCRResponse(BaseModel):
    results: list[OCRResult]
    total_processed: int
    successful: int
    failed: int


class UploadOCRResponse(BaseModel):
    status: OCRStatus
    text: str | None = None
    error: str | None = None
    pages: int | None = None
    filename: str
