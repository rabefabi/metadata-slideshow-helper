"""Image platform for Metadata Slideshow Helper."""

from __future__ import annotations

import logging
import os
import secrets
from collections import deque
from typing import cast

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import CONF_MEDIA_DIR, DATA_CONFIG, DATA_COORDINATOR, DOMAIN, TITLE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the image entity."""

    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator = data.get(DATA_COORDINATOR)
    media_dir = data.get(DATA_CONFIG, {}).get(CONF_MEDIA_DIR)

    if coordinator and media_dir:
        async_add_entities([SlideshowImageEntity(coordinator, entry.entry_id, media_dir)])


class SlideshowImageEntity(CoordinatorEntity, ImageEntity):
    """Image entity exposing the current slideshow image."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_icon = "mdi:image"
    _attr_should_poll = False

    def __init__(self, coordinator, entry_id: str, media_dir: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._media_dir = media_dir
        self._attr_unique_id = f"{entry_id}_slideshow_image"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)}, name=TITLE)
        # ImageEntity expects access_tokens as a deque for state attributes
        self.access_tokens: deque[str] = deque()
        self._ensure_token()
        self._last_path: str | None = None

    def _ensure_token(self) -> None:
        """Ensure at least one access token exists."""

        if not self.access_tokens:
            self.access_tokens.append(secrets.token_hex(8))

    async def async_image(self) -> bytes | None:
        """Return bytes of current image for the API."""

        coordinator_data = self.coordinator.data or {}
        current_path = coordinator_data.get("current_path")
        if not current_path:
            _LOGGER.warning(
                "async_image called with no current_path; coordinator data keys=%s",
                list(coordinator_data.keys()),
            )
            return None

        def _read(path: str) -> bytes | None:
            try:
                if not os.path.isfile(path):
                    _LOGGER.error("Image path is not a file: %s", path)
                    return None

                file_size = os.path.getsize(path)
                if file_size == 0:
                    _LOGGER.error("Image file is empty (0 bytes): %s", path)
                    return None

                with open(path, "rb") as file:
                    data = file.read()
                    if len(data) == 0:
                        _LOGGER.error("Read 0 bytes despite file size %d: %s", file_size, path)
                    return data
            except FileNotFoundError:
                _LOGGER.error("Current image not found: %s", path)
            except PermissionError as err:
                _LOGGER.error("Permission denied reading image %s: %s", path, err)
            except Exception as err:  # pragma: no cover - unexpected I/O errors
                _LOGGER.error("Error reading image %s: %s", path, err)
            return None

        try:
            image_bytes = cast(
                bytes | None, await self.hass.async_add_executor_job(_read, current_path)
            )
            if image_bytes is None:
                _LOGGER.error("async_image failed to read data for %s", current_path)
            elif len(image_bytes) == 0:
                _LOGGER.error(
                    "async_image read 0 bytes from %s (file exists but empty)", current_path
                )
            return image_bytes
        except Exception as err:  # pragma: no cover - unexpected executor errors
            _LOGGER.exception("async_image executor failure for %s: %s", current_path, err)
            return None

    @property
    def image_content_type(self) -> str:
        """Return mime type guessed from extension."""

        data = self.coordinator.data or {}
        current_path = data.get("current_path")
        ext = os.path.splitext(current_path or "")[1].lower()
        return "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # Initialize last path and timestamp to force initial fetch
        data = self.coordinator.data or {}
        self._last_path = data.get("current_path")
        # Set initial timestamp so frontend fetches image bytes
        self._attr_image_last_updated = dt_util.utcnow()
        self.async_write_ha_state()

    def _handle_coordinator_update(self) -> None:
        # Bump image_last_updated when the current_path changes
        coordinator_data = self.coordinator.data or {}
        current_path = coordinator_data.get("current_path")
        if current_path != self._last_path:
            self._attr_image_last_updated = dt_util.utcnow()
            self._last_path = current_path
        super()._handle_coordinator_update()
