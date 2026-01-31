from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import (
    DATA_COORDINATOR,
    DATA_DISCOVERED_IMAGE_COUNT,
    DATA_FAILED_IMAGE_COUNT,
    DATA_MATCHING_IMAGE_COUNT,
    DATA_NON_IMAGE_FILE_COUNT,
    DOMAIN,
    TITLE,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    # If a coordinator is present in hass.data, use it to create sensors.
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator: DataUpdateCoordinator | None = data.get(DATA_COORDINATOR)
    if coordinator:
        async_add_entities(
            [
                MatchingImageCountSensor(coordinator, entry.entry_id),
                DiscoveredImageCountSensor(coordinator, entry.entry_id),
                FailedImageCountSensor(coordinator, entry.entry_id),
                NonImageFileCountSensor(coordinator, entry.entry_id),
            ],
            True,
        )
    else:
        async_add_entities([])


class MatchingImageCountSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: DataUpdateCoordinator, entry_id: str):
        super().__init__(coordinator)
        self._attr_name = "Matching Image Count"
        self._attr_unique_id = f"{entry_id}_matching_image_count"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)}, name=TITLE)
        self._attr_icon = "mdi:image-multiple"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_state_class = SensorStateClass.TOTAL

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get(DATA_MATCHING_IMAGE_COUNT, 0)

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        return {
            "matching_image_count": data.get(DATA_MATCHING_IMAGE_COUNT, 0),
            "discovered_image_count": data.get(DATA_DISCOVERED_IMAGE_COUNT, 0),
        }

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success


class DiscoveredImageCountSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: DataUpdateCoordinator, entry_id: str):
        super().__init__(coordinator)
        self._attr_name = "Discovered Image Count"
        self._attr_unique_id = f"{entry_id}_discovered_count"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)}, name=TITLE)
        self._attr_icon = "mdi:image-search"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_state_class = SensorStateClass.TOTAL

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get(DATA_DISCOVERED_IMAGE_COUNT, 0)

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success


class FailedImageCountSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: DataUpdateCoordinator, entry_id: str):
        super().__init__(coordinator)
        self._attr_name = "Failed Image Count"
        self._attr_unique_id = f"{entry_id}_failed_count"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)}, name=TITLE)
        self._attr_icon = "mdi:image-broken"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_state_class = SensorStateClass.TOTAL

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get(DATA_FAILED_IMAGE_COUNT, 0)

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success


class NonImageFileCountSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: DataUpdateCoordinator, entry_id: str):
        super().__init__(coordinator)
        self._attr_name = "Non-Image File Count"
        self._attr_unique_id = f"{entry_id}_non_image_count"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)}, name=TITLE)
        self._attr_icon = "mdi:file-multiple"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_state_class = SensorStateClass.TOTAL

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get(DATA_NON_IMAGE_FILE_COUNT, 0)

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success
