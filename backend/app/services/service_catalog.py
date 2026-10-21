"""Canonical registry of supported external API integrations.

This module is the single source of truth for:

* which service names exist,
* how each one is labelled for humans,
* the request parameters each one accepts,
* the client class that talks to the upstream provider.

The dashboard consumes this over ``GET /api/v1/external-services/supported``
so the provider list is never duplicated in the frontend. Adding a service
means adding one entry here.
"""

from dataclasses import dataclass
from typing import Any, Optional, Type, Union, get_args, get_origin

from pydantic import BaseModel

from app.external_apis.base import BaseAPIClient
from app.external_apis.news_api import NewsAPIClient
from app.external_apis.stock_api import StockAPIClient
from app.external_apis.weather_api import WeatherAPIClient
from app.schemas.service_params import (
    NewsParams,
    ServiceParams,
    StockParams,
    WeatherParams,
)


@dataclass(frozen=True)
class ServiceDefinition:
    """Everything the platform knows about one supported external API."""

    service_name: str
    label: str
    description: str
    signup_url: str
    docs_url: str
    client_cls: Type[BaseAPIClient]
    params_model: Type[ServiceParams]
    example: dict[str, Any]
    required_params: str


SERVICE_CATALOG: dict[str, ServiceDefinition] = {
    "weather": ServiceDefinition(
        service_name="weather",
        label="OpenWeatherMap",
        description="Current weather conditions for a city or coordinate pair.",
        signup_url="https://home.openweathermap.org/users/sign_up",
        docs_url="https://openweathermap.org/api",
        client_cls=WeatherAPIClient,
        params_model=WeatherParams,
        example={"city": "London"},
        required_params="city OR (lat AND lon)",
    ),
    "news": ServiceDefinition(
        service_name="news",
        label="NewsAPI",
        description="Recent news articles matching a free-text query.",
        signup_url="https://newsapi.org/register",
        docs_url="https://newsapi.org",
        client_cls=NewsAPIClient,
        params_model=NewsParams,
        example={"query": "artificial intelligence"},
        required_params="query",
    ),
    "stock": ServiceDefinition(
        service_name="stock",
        label="Alpha Vantage",
        description="Latest global quote for a ticker symbol.",
        signup_url="https://www.alphavantage.co/support/#api-key",
        docs_url="https://www.alphavantage.co/documentation/",
        client_cls=StockAPIClient,
        params_model=StockParams,
        example={"symbol": "AAPL"},
        required_params="symbol",
    ),
}


def get_service(service_name: str) -> Optional[ServiceDefinition]:
    """Return the catalog entry for a service name, or None if unsupported."""
    return SERVICE_CATALOG.get(service_name)


def supported_service_names() -> list[str]:
    """Return the supported service names in stable order."""
    return list(SERVICE_CATALOG.keys())


def _unwrap_optional(annotation: Any) -> Any:
    """Strip Optional[...] down to the underlying type."""
    if get_origin(annotation) is Union:
        args = [a for a in get_args(annotation) if a is not type(None)]
        if len(args) == 1:
            return args[0]
    return annotation


def _json_type(annotation: Any) -> str:
    """Map a Python annotation to a JSON-ish type name for the UI."""
    annotation = _unwrap_optional(annotation)
    if annotation is bool:
        return "boolean"
    if annotation is int:
        return "number"
    if annotation is float:
        return "number"
    if annotation is str:
        return "string"
    return "string"


def _param_spec(params_model: Type[BaseModel]) -> dict[str, dict[str, Any]]:
    """Describe a params model as a field -> metadata mapping."""
    spec: dict[str, dict[str, Any]] = {}
    for name, field in params_model.model_fields.items():
        entry: dict[str, Any] = {
            "type": _json_type(field.annotation),
            "required": field.is_required(),
        }
        if field.description:
            entry["description"] = field.description
        if not field.is_required() and field.default is not None:
            entry["default"] = field.default
        example = (params_model.model_fields[name].json_schema_extra or {}).get(
            "examples"
        )
        if example:
            entry["example"] = example
        spec[name] = entry
    return spec


def describe_service(definition: ServiceDefinition) -> dict[str, Any]:
    """Build the JSON payload published by ``GET /external-services/supported``."""
    return {
        "service_name": definition.service_name,
        "label": definition.label,
        "description": definition.description,
        "signup_url": definition.signup_url,
        "docs_url": definition.docs_url,
        "required_params": definition.required_params,
        "example": definition.example,
        "params": _param_spec(definition.params_model),
    }


def describe_all_services() -> list[dict[str, Any]]:
    """Describe every supported service, in stable order."""
    return [describe_service(defn) for defn in SERVICE_CATALOG.values()]
