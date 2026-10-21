"""Registry of supported external API clients.

Derived from the service catalog so the client map and the published
catalogue can never drift apart.
"""

from app.services.service_catalog import SERVICE_CATALOG

CLIENT_REGISTRY: dict[str, type] = {
    name: definition.client_cls for name, definition in SERVICE_CATALOG.items()
}
