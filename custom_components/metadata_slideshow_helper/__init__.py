"""Metadata Slideshow Helper integration."""

from __future__ import annotations

# ruff: noqa: PLC0415 (import-outside-toplevel) - avoid heavy imports on package import
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import timedelta
from typing import TYPE_CHECKING

from .const import AdvanceMode
from .scanner import MediaScanner

# Only import Home Assistant types for type checking; runtime imports occur in functions
if TYPE_CHECKING:  # pragma: no cover - typing only
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor", "image"]


@dataclass
class AdvancementState:
    """Holds the state of image advancement."""

    advance_index: int = 0
    last_advance: float = field(default_factory=time.time)
    smart_random_counter: int = 0


class SlideshowCoordinator:
    """Handles image advancement for the slideshow."""

    def __init__(
        self,
        hass: HomeAssistant,
        scanner: MediaScanner,
        advance_interval: float,
        advance_mode: AdvanceMode,
        smart_random_sequence_length: int,
    ):
        self.hass = hass
        self.scanner = scanner
        self.advance_interval = advance_interval
        self.advance_mode = advance_mode
        self.smart_random_sequence_length = smart_random_sequence_length
        self.state = AdvancementState()

    async def async_update_data(self) -> dict:
        """Fetch and filter media, then handle image advancement."""
        from .const import (
            DATA_ADVANCE_INDEX,
            DATA_CURRENT_PATH,
            DATA_DISCOVERED_IMAGE_COUNT,
            DATA_MATCHING_IMAGE_COUNT,
            DATA_MATCHING_IMAGES,
            AdvanceMode,
        )
        from .scanner import ScanResult as _ScanResult

        scan_result: _ScanResult = await self.hass.async_add_executor_job(
            self.scanner.scan_and_filter,
        )
        matching_items = scan_result.matching

        # Auto-advance to next image based on elapsed time
        current_time = time.time()
        time_since_advance = current_time - self.state.last_advance

        if matching_items and time_since_advance >= self.advance_interval:
            if self.advance_mode == AdvanceMode.SMART_RANDOM:
                # In smart random mode, advance sequentially through
                # smart_random_sequence_length images, then jump to a new random position
                self.state.smart_random_counter += 1
                if self.state.smart_random_counter >= self.smart_random_sequence_length:
                    # Jump to a new random image
                    self.state.advance_index = random.randint(0, len(matching_items) - 1)
                    self.state.smart_random_counter = 0
                    _LOGGER.debug(
                        f"Smart random: jumped to image index {self.state.advance_index}, "
                        f"will advance sequentially for {self.smart_random_sequence_length} images"
                    )
            elif self.advance_mode != AdvanceMode.SEQUENTIAL:
                msg = (
                    f"Unknown advance_mode: {self.advance_mode}. Expected "
                    f"'{AdvanceMode.SEQUENTIAL.value}' or '{AdvanceMode.SMART_RANDOM.value}'."
                )
                raise ValueError(msg)

            self.state.advance_index = (self.state.advance_index + 1) % len(matching_items)
            self.state.last_advance = current_time

        # Ensure index is valid
        if matching_items:
            self.state.advance_index = self.state.advance_index % len(matching_items)
            current_path = matching_items[self.state.advance_index].path
        else:
            current_path = None

        return {
            DATA_MATCHING_IMAGES: matching_items,
            DATA_MATCHING_IMAGE_COUNT: scan_result.matching_count,
            DATA_DISCOVERED_IMAGE_COUNT: scan_result.discovered_count,
            DATA_CURRENT_PATH: current_path,
            DATA_ADVANCE_INDEX: self.state.advance_index,
        }


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Import integration modules at runtime to avoid heavy imports on package import
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

    from .const import (
        CONF_ADVANCE_INTERVAL,
        CONF_ADVANCE_MODE,
        CONF_EXCLUDE_TAGS,
        CONF_INCLUDE_TAGS,
        CONF_MEDIA_DIR,
        CONF_MIN_RATING,
        CONF_REFRESH_INTERVAL,
        CONF_SMART_RANDOM_SEQUENCE_LENGTH,
        DATA_CONFIG,
        DATA_COORDINATOR,
        DEFAULT_ADVANCE_INTERVAL,
        DEFAULT_ADVANCE_MODE,
        DEFAULT_RESCAN_INTERVAL,
        DEFAULT_SMART_RANDOM_SEQUENCE_LENGTH,
        DOMAIN,
        AdvanceMode,
    )
    from .scanner import MediaScanner

    hass.data.setdefault(DOMAIN, {})
    _LOGGER.info(f"{DOMAIN} starting")

    # Parse configuration
    media_dir_str = entry.data.get(CONF_MEDIA_DIR, "")
    rescan_interval = entry.data.get(CONF_REFRESH_INTERVAL, DEFAULT_RESCAN_INTERVAL)
    advance_interval = entry.data.get(CONF_ADVANCE_INTERVAL, DEFAULT_ADVANCE_INTERVAL)
    advance_mode = AdvanceMode(entry.data.get(CONF_ADVANCE_MODE, DEFAULT_ADVANCE_MODE.value))

    smart_random_sequence_length = entry.data.get(
        CONF_SMART_RANDOM_SEQUENCE_LENGTH, DEFAULT_SMART_RANDOM_SEQUENCE_LENGTH
    )

    min_rating = entry.data.get(CONF_MIN_RATING, 0)
    include_tags_str = entry.data.get(CONF_INCLUDE_TAGS, "")
    exclude_tags_str = entry.data.get(CONF_EXCLUDE_TAGS, "")

    # Parse comma-separated directories and tags
    media_dirs = [d.strip() for d in media_dir_str.split(",") if d.strip()]
    include_tags = [t.strip() for t in include_tags_str.split(",") if t.strip()]
    exclude_tags = [t.strip() for t in exclude_tags_str.split(",") if t.strip()]

    # Create media scanner with filter configuration
    scanner = MediaScanner(
        roots=media_dirs,
        include_tags=include_tags,
        exclude_tags=exclude_tags,
        min_rating=min_rating,
        rescan_interval=rescan_interval,
    )

    # Create the slideshow coordinator
    slideshow_coordinator = SlideshowCoordinator(
        hass=hass,
        scanner=scanner,
        advance_interval=advance_interval,
        advance_mode=advance_mode,
        smart_random_sequence_length=smart_random_sequence_length,
    )

    # Coordinator update frequency should be frequent enough to handle image advancement,
    # while respecting the configured rescan interval.
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{entry.entry_id}",
        update_method=slideshow_coordinator.async_update_data,
        update_interval=timedelta(seconds=advance_interval),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONFIG: entry.data,
        DATA_COORDINATOR: coordinator,
    }

    # Listen for options updates and force rescan
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload integration when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    from .const import DOMAIN

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
