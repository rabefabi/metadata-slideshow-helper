from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN, TITLE


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    # If a coordinator is present in hass.data, use it to create sensors.
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator: DataUpdateCoordinator | None = data.get("coordinator")
    if coordinator:
        async_add_entities(
            [
                SlideshowImageCountSensor(coordinator, entry.entry_id),
                SlideshowCurrentImageSensor(coordinator, entry.entry_id),
            ],
            True,
        )
    else:
        async_add_entities([])


class SlideshowImageCountSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: DataUpdateCoordinator, entry_id: str):
        super().__init__(coordinator)
        self._attr_name = "Slideshow Image Count"
        self._attr_unique_id = f"{entry_id}_image_count"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)}, name=TITLE
        )
        self._attr_icon = "mdi:image-multiple"

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get("count", 0)

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        images = data.get("images", [])
        return {
            "total_images": data.get("count", 0),
            "sample_images": [img.path for img in images[:5]],
        }

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success


class SlideshowCurrentImageSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: DataUpdateCoordinator, entry_id: str):
        super().__init__(coordinator)
        self._attr_name = "Slideshow Current Image"
        self._attr_unique_id = f"{entry_id}_current_image"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)}, name=TITLE
        )
        self._attr_icon = "mdi:image"

    @property
    def native_value(self):
        current = (self.coordinator.data or {}).get("current_url")
        return current if current else STATE_UNKNOWN

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        return {
            "cycle_index": data.get("cycle_index", 0),
            "total_images": data.get("count", 0),
        }

    @property
    def entity_picture(self) -> str | None:
        """Return the entity picture to represent current image."""
        current = self.native_value
        return current if current != STATE_UNKNOWN else None

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success
