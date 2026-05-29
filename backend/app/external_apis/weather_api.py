"""OpenWeatherMap API client."""

from datetime import datetime, timezone

import httpx

from app.external_apis.base import BaseAPIClient
from app.utils.exceptions import ExternalAPIError

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


class WeatherAPIClient(BaseAPIClient):
    """Client for OpenWeatherMap current weather data."""

    service_name = "weather"

    def __init__(self, encrypted_api_key: str) -> None:
        from app.utils.encryption import decrypt

        self._api_key = decrypt(encrypted_api_key)

    def validate_params(self, params: dict) -> bool:
        if params.get("city"):
            return True
        return params.get("lat") is not None and params.get("lon") is not None

    async def fetch(self, params: dict) -> dict:
        if not self.validate_params(params):
            raise ExternalAPIError("weather requires 'city' or 'lat' and 'lon'")

        query_params: dict = {"appid": self._api_key, "units": "metric"}
        if params.get("city"):
            query_params["q"] = params["city"]
        else:
            query_params["lat"] = params["lat"]
            query_params["lon"] = params["lon"]

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(WEATHER_URL, params=query_params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            raise ExternalAPIError(
                f"Weather API returned {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise ExternalAPIError("Weather API request failed") from exc

        main = payload.get("main", {})
        wind = payload.get("wind", {})
        weather = (payload.get("weather") or [{}])[0]

        return {
            "service": self.service_name,
            "data": {
                "city": payload.get("name"),
                "temperature_c": main.get("temp"),
                "humidity": main.get("humidity"),
                "description": weather.get("description"),
                "wind_speed": wind.get("speed"),
            },
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
