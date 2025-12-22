from __future__ import annotations

from typing import Any, cast

from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)

from .api import FeedFormatter
from .const import CONF_EXCLUDE_TAGS, CONF_INCLUDE_TAGS, CONF_MEDIA_DIR, CONF_MIN_RATING, DOMAIN
from .scanner import MediaScanner, apply_filters


async def async_register_services(hass: HomeAssistant):
    async def handle_get_image_urls(call: ServiceCall) -> ServiceResponse:
        # Parse tags from input (can be list or comma-separated string)
        include_raw = call.data.get(CONF_INCLUDE_TAGS) or []
        exclude_raw = call.data.get(CONF_EXCLUDE_TAGS) or []

        # Convert to list if string
        if isinstance(include_raw, str):
            include = [t.strip() for t in include_raw.split(",") if t.strip()]
        else:
            include = include_raw

        if isinstance(exclude_raw, str):
            exclude = [t.strip() for t in exclude_raw.split(",") if t.strip()]
        else:
            exclude = exclude_raw

        min_rating = int(call.data.get(CONF_MIN_RATING) or 0)

        domains = hass.data.get(DOMAIN, {})
        if not domains:
            return {"error": "No integration configured", "images": [], "count": 0}

        _, entry_data = next(iter(domains.items()))
        media_dir = entry_data.get("config", {}).get(CONF_MEDIA_DIR)
        if not media_dir:
            return {"error": "No media directory configured", "images": [], "count": 0}

        # Scan and filter
        scanner = MediaScanner(media_dir)
        items = await hass.async_add_executor_job(scanner.scan)
        filtered = apply_filters(items, include, exclude, min_rating)

        fmt = FeedFormatter()
        urls = fmt.to_urls(filtered)

        # Set state for legacy access
        # Attributes are JSON-compatible; cast to satisfy type checker
        hass.states.async_set(
            f"{DOMAIN}.image_feed",
            len(urls),
            cast(dict[str, Any], {"total": len(urls)}),
        )

        # Return response for Developer Tools
        resp: Any = {
            "images": urls,
            "count": len(urls),
            "filters": {
                "include_tags": include,
                "exclude_tags": exclude,
                "min_rating": min_rating,
            },
        }
        return cast(ServiceResponse, resp)

    hass.services.async_register(
        DOMAIN, "get_image_urls", handle_get_image_urls, supports_response=SupportsResponse.ONLY
    )
