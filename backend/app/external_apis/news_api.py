"""NewsAPI client."""

from datetime import datetime, timezone

import httpx

from app.external_apis.base import BaseAPIClient
from app.utils.exceptions import ExternalAPIError

NEWS_URL = "https://newsapi.org/v2/everything"


class NewsAPIClient(BaseAPIClient):
    """Client for NewsAPI everything endpoint."""

    service_name = "news"

    def __init__(self, encrypted_api_key: str) -> None:
        from app.utils.encryption import decrypt

        self._api_key = decrypt(encrypted_api_key)

    def validate_params(self, params: dict) -> bool:
        return bool(params.get("query"))

    async def fetch(self, params: dict) -> dict:
        if not self.validate_params(params):
            raise ExternalAPIError("news requires 'query'")

        query_params = {
            "q": params["query"],
            "language": params.get("language", "en"),
            "pageSize": 5,
            "apiKey": self._api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(NEWS_URL, params=query_params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            raise ExternalAPIError(f"News API returned {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise ExternalAPIError("News API request failed") from exc

        articles = []
        for article in (payload.get("articles") or [])[:5]:
            source = article.get("source") or {}
            articles.append(
                {
                    "title": article.get("title"),
                    "source": source.get("name") if isinstance(source, dict) else source,
                    "url": article.get("url"),
                    "published_at": article.get("publishedAt"),
                }
            )

        return {
            "service": self.service_name,
            "data": {
                "query": params["query"],
                "total_results": payload.get("totalResults", len(articles)),
                "articles": articles,
            },
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
