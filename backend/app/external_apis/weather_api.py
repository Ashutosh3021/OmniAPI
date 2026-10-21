"""OpenWeatherMap API client."""

from datetime import datetime, timezone

import httpx

from app.external_apis.base import BaseAPIClient
from app.external_apis.client_pool import get_client
from app.schemas.service_params import WeatherParams
from app.utils.exceptions import ExternalAPIError

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


class WeatherAPIClient(BaseAPIClient):
    """Client for OpenWeatherMap current weather data."""

    service_name = "weather"
    params_model = WeatherParams

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
            client = get_client()
            response = await client.get(WEATHER_URL, params=query_params)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            # 4xx (other than 408/429) means the request itself is wrong;
            # retrying it will not help.
            retryable = status_code >= 500 or status_code in (408, 429)
            raise ExternalAPIError(
                f"Weather API returned {status_code}", retryable=retryable
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
