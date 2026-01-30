"""Metadata Slideshow Helper integration."""

from __future__ import annotations

# ruff: noqa: PLC0415 (import-outside-toplevel) - avoid heavy imports on package import
import logging
import time
from datetime import timedelta
from typing import TYPE_CHECKING

# Only import Home Assistant types for type checking; runtime imports occur in functions
if TYPE_CHECKING:  # pragma: no cover - typing only
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor", "image"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:  # noqa: PLR0915 (too many statements) - consider refactoring if this function grows further
    # Import integration modules at runtime to avoid heavy imports on package import
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

    from .const import (
        CONF_ADVANCE_INTERVAL,
        CONF_EXCLUDE_TAGS,
        CONF_INCLUDE_TAGS,
        CONF_MEDIA_DIR,
        CONF_MIN_RATING,
        CONF_REFRESH_INTERVAL,
        DATA_ADVANCE_INDEX,
        DATA_CONFIG,
        DATA_COORDINATOR,
        DATA_CURRENT_PATH,
        DATA_DISCOVERED_IMAGE_COUNT,
        DATA_MATCHING_IMAGE_COUNT,
        DATA_MATCHING_IMAGES,
        DEFAULT_ADVANCE_INTERVAL,
        DEFAULT_REFRESH_INTERVAL,
        DOMAIN,
    )
    from .scanner import MediaScanner, apply_filters

    hass.data.setdefault(DOMAIN, {})
    _LOGGER.info(f"{DOMAIN} starting")

    # Create coordinator that scans media directory
    media_dir_str = entry.data.get(CONF_MEDIA_DIR, "")
    refresh_interval = entry.data.get(CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL)
    advance_interval = entry.data.get(CONF_ADVANCE_INTERVAL, DEFAULT_ADVANCE_INTERVAL)

    min_rating = entry.data.get(CONF_MIN_RATING, 0)
    include_tags_str = entry.data.get(CONF_INCLUDE_TAGS, "")
    exclude_tags_str = entry.data.get(CONF_EXCLUDE_TAGS, "")

    # Parse comma-separated directories and tags
    media_dirs = [d.strip() for d in media_dir_str.split(",") if d.strip()]
    include_tags = [t.strip() for t in include_tags_str.split(",") if t.strip()]
    exclude_tags = [t.strip() for t in exclude_tags_str.split(",") if t.strip()]

    # Image advancement state
    advance_index: int = 0
    last_advance: float = time.time()
    cached_matching_items: list = []
    last_rescan: float = 0.0
    last_discovered_count: int = 0
    # Track if we've already warned about no images to avoid log spam
    no_images_warned: bool = False

    async def async_update_data():
        """Fetch data from media scanner and handle image cycling."""

        # TODO: Refactor to avoid use of nonlocal, use dedicated class to hold state instead
        # https://github.com/rabefabi/metadata-slideshow-helper/issues/9
        nonlocal \
            last_advance, \
            advance_index, \
            cached_matching_items, \
            last_rescan, \
            last_discovered_count, \
            no_images_warned

        current_time = time.time()

        # Only rescan filesystem periodically, not every coordinator update
        if not media_dirs:
            matching_items = []
        elif not cached_matching_items or (current_time - last_rescan) >= float(refresh_interval):
            _LOGGER.info(f"Rescanning media_dirs: {media_dirs}")
            scanner = MediaScanner(media_dirs)
            discovered_items = await hass.async_add_executor_job(scanner.scan)
            # Apply filters based on configuration
            matching_items = apply_filters(discovered_items, include_tags, exclude_tags, min_rating)
            cached_matching_items = matching_items
            last_rescan = current_time
            last_discovered_count = len(discovered_items)
            if matching_items:
                _LOGGER.info(
                    f"Found {len(matching_items)} matching images (from {len(discovered_items)} discovered images, "
                    f"min_rating={min_rating}, include_tags={include_tags}, exclude_tags={exclude_tags})"
                )
                no_images_warned = False  # Reset warning flag when images are found
            elif not no_images_warned:
                # Only log warning once when no images match the filters
                _LOGGER.warning(
                    f"No images matched filters in {media_dirs} "
                    f"(discovered {len(discovered_items)} images, min_rating={min_rating}, "
                    f"include_tags={include_tags}, exclude_tags={exclude_tags})"
                )
                no_images_warned = True
        else:
            matching_items = cached_matching_items

        # Auto-advance to next image based on elapsed time
        time_since_advance = current_time - last_advance

        if matching_items and time_since_advance >= advance_interval:
            # TODO: Consider a "smart random" mode, which does a pre-configured amount of images in a row, and then jumps to a random image
            # https://github.com/rabefabi/metadata-slideshow-helper/issues/10
            advance_index = (advance_index + 1) % len(matching_items)
            last_advance = current_time

        # Ensure index is valid
        if matching_items:
            advance_index = advance_index % len(matching_items)
            current_path = matching_items[advance_index].path
        else:
            current_path = None

        # TODO: Consider adding dataclass for return type
        # https://github.com/rabefabi/metadata-slideshow-helper/issues/9
        return {
            DATA_MATCHING_IMAGES: matching_items,
            DATA_MATCHING_IMAGE_COUNT: len(matching_items),
            DATA_DISCOVERED_IMAGE_COUNT: last_discovered_count,
            DATA_CURRENT_PATH: current_path,
            DATA_ADVANCE_INDEX: advance_index,
        }

    # Coordinator update frequency should be frequent enough to handle image advancement,
    # while respecting the configured refresh interval.
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{entry.entry_id}",
        update_method=async_update_data,
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
