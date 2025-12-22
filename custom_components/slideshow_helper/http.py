"""HTTP endpoints for slideshow images."""

from __future__ import annotations

import logging
import os

from aiohttp import web
from homeassistant.components.http import KEY_HASS, HomeAssistantView
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class SlideshowImageView(HomeAssistantView):
    """Serve slideshow images."""

    url = "/api/slideshow_helper/{entry_id}/{image_path}"
    name = "api:slideshow_helper:image"
    requires_auth = False

    async def get(self, request: web.Request, entry_id: str, image_path: str) -> web.Response:
        """Return image bytes."""

        # Decode the image path (it will be URL-encoded)
        image_path = image_path.replace("_SLASH_", "/")

        hass: HomeAssistant = request.app[KEY_HASS]
        data = hass.data.get("slideshow_helper", {}).get(entry_id, {})
        media_dir = data.get("config", {}).get("media_dir")

        _LOGGER.debug(
            f"HTTP view request: entry_id={entry_id}, image_path={image_path}, media_dir={media_dir}"
        )

        if not media_dir:
            _LOGGER.error("Media directory not configured")
            raise web.HTTPNotFound()

        full_path = os.path.join(media_dir, image_path)
        _LOGGER.debug(f"Serving image from: {full_path}, exists={os.path.isfile(full_path)}")

        # Prevent directory traversal
        if not os.path.abspath(full_path).startswith(os.path.abspath(media_dir)):
            raise web.HTTPForbidden()

        if not os.path.isfile(full_path):
            _LOGGER.error(f"Image not found: {full_path}")
            raise web.HTTPNotFound()

        def _read_file(path: str) -> bytes:
            with open(path, "rb") as f:
                return f.read()

        try:
            data = await hass.async_add_executor_job(_read_file, full_path)

            # Determine content type
            ext = os.path.splitext(full_path)[1].lower()
            content_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"

            return web.Response(body=data, content_type=content_type)
        except Exception as err:
            _LOGGER.error(f"Error serving image: {err}")
            raise web.HTTPInternalServerError() from err
