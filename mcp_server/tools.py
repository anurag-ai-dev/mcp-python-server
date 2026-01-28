from fastmcp.tools import tool

from mcp_server.helpers import format_alert, make_nws_request
from settings import settings


@tool(name="get_alerts", description="Get weather alerts for a US state.")
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two letter US state code (eg. CA, NY).
    """
    url = f"{settings.NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts found for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)


@tool(name="get_forecast", description="Get weather forecast for a specific location.")
async def get_forecast(latitude: str, longitude: str) -> str:
    """Get weather forecast for a specific location.

    Args:
        latitude: Latitude of the location.
        longitude: Longitude of the location.
    """
    points_url = f"{settings.NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable string
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  #  Only show next 5 periods
        forecast = f"""
        {period["name"]}:
        Temperature: {period["temperature"]}°{period["temperatureUnit"]}
        Wind: {period["windSpeed"]} {period["windDirection"]}
        Forecast: {period["detailedForecast"]}
        """
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)
