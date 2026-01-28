from typing import Any

import httpx

from settings import settings
from utils.logger import get_logger

logger = get_logger()


async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {"User-Agent": settings.USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error("Error making request to NWS API", extra={"error": e})
            return None


def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    properties = feature["properties"]
    return f"""
Event: {properties["event"]}
Area: {properties["areaDesc"]}
Severity: {properties["severity"]}
Description: {properties["description"]}
Instructions: {properties["instruction"]}
"""
