"""Alpha Vantage stock quote client."""

from datetime import datetime, timezone

import httpx

from app.external_apis.base import BaseAPIClient
from app.external_apis.client_pool import get_client
from app.schemas.service_params import StockParams
from app.utils.exceptions import ExternalAPIError

STOCK_URL = "https://www.alphavantage.co/query"


class StockAPIClient(BaseAPIClient):
    """Client for Alpha Vantage GLOBAL_QUOTE endpoint."""

    service_name = "stock"
    params_model = StockParams

    def __init__(self, encrypted_api_key: str) -> None:
        from app.utils.encryption import decrypt

        self._api_key = decrypt(encrypted_api_key)

    def validate_params(self, params: dict) -> bool:
        return bool(params.get("symbol"))

    async def fetch(self, params: dict) -> dict:
        if not self.validate_params(params):
            raise ExternalAPIError("stock requires 'symbol'")

        symbol = str(params["symbol"]).upper()
        query_params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self._api_key,
        }

        try:
            client = get_client()
            response = await client.get(STOCK_URL, params=query_params)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            # 4xx (other than 408/429) means the request itself is wrong;
            # retrying it will not help.
            retryable = status_code >= 500 or status_code in (408, 429)
            raise ExternalAPIError(self.upstream_error(status_code), retryable=retryable) from exc
        except httpx.HTTPError as exc:
            raise ExternalAPIError("Stock API request failed") from exc

        if "Error Message" in payload or "Note" in payload:
            message = payload.get("Error Message") or payload.get("Note")
            raise ExternalAPIError(str(message))

        quote = payload.get("Global Quote") or {}
        if not quote:
            raise ExternalAPIError("No quote data returned for symbol")

        return {
            "service": self.service_name,
            "data": {
                "symbol": quote.get("01. symbol", symbol),
                "price": quote.get("05. price"),
                "change": quote.get("09. change"),
                "change_percent": quote.get("10. change percent"),
                "volume": quote.get("06. volume"),
            },
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
