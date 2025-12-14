"""Image platform for slideshow helper."""

from __future__ import annotations

import logging
import os
import secrets
from collections import deque
from typing import ClassVar

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the image entity."""

    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator = data.get("coordinator")
    media_dir = data.get("config", {}).get("media_dir")

    if coordinator and media_dir:
        async_add_entities([SlideshowImageEntity(coordinator, entry.entry_id, media_dir)])


class SlideshowImageEntity(CoordinatorEntity, ImageEntity):
    """Image entity exposing the current slideshow image."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_icon = "mdi:image"
    _attr_access_tokens: ClassVar[set[str]] = set()
    _attr_should_poll = False

    def __init__(self, coordinator, entry_id: str, media_dir: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._media_dir = media_dir
        self._attr_unique_id = f"{entry_id}_slideshow_image"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)}, name="Slideshow Helper")
        # ImageEntity expects access_tokens as a deque for state attributes
        self.access_tokens: deque[str] = deque()
        self._ensure_token()
        self._last_path: str | None = None

    def _ensure_token(self) -> None:
        """Ensure at least one access token exists."""

        if not self.access_tokens:
            self.access_tokens.append(secrets.token_hex(8))

    @property
    def extra_state_attributes(self):
        """Provide extra attributes including cycle index and count."""

        data = self.coordinator.data or {}
        return {
            "cycle_index": data.get("cycle_index"),
            "total_images": data.get("count"),
        }

    @property
    def state(self):
        """Expose last updated timestamp as state so HA sees changes.

        Returning a stable value keeps `last_changed` constant; by using
        the ISO timestamp we ensure the entity state changes alongside
        `image_last_updated`, which helps Lovelace cards refresh.
        """

        if self._attr_image_last_updated is None:
            return STATE_UNKNOWN
        return self._attr_image_last_updated.isoformat()

    @property
    def image_url(self) -> str | None:
        """Return None to serve bytes via async_image()."""
        self._ensure_token()
        return None

    async def async_image(self) -> bytes | None:
        """Return bytes of current image for the API."""

        data = self.coordinator.data or {}
        current_path = data.get("current_path")
        if not current_path:
            return None

        def _read(path: str) -> bytes | None:
            try:
                with open(path, "rb") as file:
                    return file.read()
            except FileNotFoundError:
                _LOGGER.warning("Current image not found: %s", path)
            except Exception as err:  # pragma: no cover - unexpected I/O errors
                _LOGGER.error("Error reading image %s: %s", path, err)
            return None

        return await self.hass.async_add_executor_job(_read, current_path)

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
        from homeassistant.util import dt as dt_util
        self._attr_image_last_updated = dt_util.utcnow()
        # Keep state in sync with the initial timestamp
        self._attr_state = self._attr_image_last_updated.isoformat()
        self.async_write_ha_state()

    def _handle_coordinator_update(self) -> None:
        # Bump image_last_updated when the current_path changes
        data = self.coordinator.data or {}
        current_path = data.get("current_path")
        if current_path != self._last_path:
            from homeassistant.util import dt as dt_util
            self._attr_image_last_updated = dt_util.utcnow()
            self._attr_state = self._attr_image_last_updated.isoformat()
            self._last_path = current_path
        super()._handle_coordinator_update()




