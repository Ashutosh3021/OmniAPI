"""Per-service request parameter schemas.

Each supported external API has its own parameter contract. These models are
the server-side enforcement of that contract: they are used to validate
``POST /orchestrate`` bodies and to publish the parameter metadata that the
dashboard renders when building a request.

The catalog (``app.services.service_catalog``) maps each service name to one
of these models, so adding a service means adding a model and one catalog
entry — never another hardcoded list in the frontend.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ServiceParams(BaseModel):
    """Base class for all per-service parameter models."""

    # Unknown parameters are rejected so a typo surfaces as a clear 422
    # instead of being silently forwarded to the upstream provider.
    model_config = ConfigDict(extra="forbid")


class WeatherParams(ServiceParams):
    """Parameters for the OpenWeatherMap current-weather endpoint."""

    city: Optional[str] = Field(default=None, max_length=100, examples=["London"])
    lat: Optional[float] = Field(default=None, ge=-90, le=90, examples=[51.51])
    lon: Optional[float] = Field(default=None, ge=-180, le=180, examples=[-0.13])

    @model_validator(mode="after")
    def _require_location(self) -> "WeatherParams":
        if self.city:
            if self.lat is not None or self.lon is not None:
                raise ValueError("weather accepts either 'city' or 'lat'/'lon', not both")
            return self
        if self.lat is None or self.lon is None:
            raise ValueError("weather requires 'city' or both 'lat' and 'lon'")
        return self


class NewsParams(ServiceParams):
    """Parameters for the NewsAPI /v2/everything endpoint."""

    query: str = Field(..., min_length=1, max_length=200, examples=["artificial intelligence"])
    language: str = Field(default="en", min_length=2, max_length=5, examples=["en"])


class StockParams(ServiceParams):
    """Parameters for the Alpha Vantage GLOBAL_QUOTE endpoint."""

    symbol: str = Field(..., min_length=1, max_length=10, examples=["AAPL"])
