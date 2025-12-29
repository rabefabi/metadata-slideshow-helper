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
        CONF_CYCLE_INTERVAL,
        CONF_EXCLUDE_TAGS,
        CONF_INCLUDE_TAGS,
        CONF_MEDIA_DIR,
        CONF_MIN_RATING,
        CONF_REFRESH_INTERVAL,
        DEFAULT_CYCLE_INTERVAL,
        DEFAULT_REFRESH_INTERVAL,
        DOMAIN,
    )
    from .scanner import MediaScanner, apply_filters

    hass.data.setdefault(DOMAIN, {})
    _LOGGER.info(f"{DOMAIN} starting")

    # Create coordinator that scans media directory
    media_dir = entry.data.get(CONF_MEDIA_DIR, "")
    refresh_interval = entry.data.get(CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL)
    cycle_interval = entry.data.get(CONF_CYCLE_INTERVAL, DEFAULT_CYCLE_INTERVAL)

    min_rating = entry.data.get(CONF_MIN_RATING, 0)
    include_tags_str = entry.data.get(CONF_INCLUDE_TAGS, "")
    exclude_tags_str = entry.data.get(CONF_EXCLUDE_TAGS, "")

    # Parse comma-separated tags
    include_tags = [t.strip() for t in include_tags_str.split(",") if t.strip()]
    exclude_tags = [t.strip() for t in exclude_tags_str.split(",") if t.strip()]

    # Cycling state
    cycle_index: int = 0
    last_cycle: float = time.time()
    cached_items: list = []
    last_scan: float = 0.0
    last_total_count: int
    # Track if we've already warned about no images to avoid log spam
    no_images_warned: bool = False

    async def async_update_data():
        """Fetch data from media scanner and handle cycling."""
        nonlocal \
            last_cycle, \
            cycle_index, \
            cached_items, \
            last_scan, \
            last_total_count, \
            no_images_warned

        current_time = time.time()

        # Only rescan filesystem periodically, not every update
        if not media_dir:
            items = []
        elif not cached_items or (current_time - last_scan) >= float(refresh_interval):
            _LOGGER.info(f"Scanning media_dir: {media_dir}")
            scanner = MediaScanner(media_dir)
            all_items = await hass.async_add_executor_job(scanner.scan)
            # Apply filters based on configuration
            items = apply_filters(all_items, include_tags, exclude_tags, min_rating)
            cached_items = items
            last_scan = current_time
            last_total_count = len(all_items)
            if items:
                _LOGGER.info(
                    f"Found {len(items)} images (filtered from {len(all_items)} total, "
                    f"min_rating={min_rating}, include_tags={include_tags}, exclude_tags={exclude_tags})"
                )
                no_images_warned = False  # Reset warning flag when images are found
            elif not no_images_warned:
                # Only log warning once when no images are found
                _LOGGER.warning(
                    f"No images found in {media_dir} after filtering "
                    f"(scanned {len(all_items)}, min_rating={min_rating}, "
                    f"include_tags={include_tags}, exclude_tags={exclude_tags})"
                )
                no_images_warned = True
        else:
            items = cached_items

        # Auto-cycle through images based on elapsed time
        time_since_cycle = current_time - last_cycle

        if items and time_since_cycle >= cycle_interval:
            cycle_index = (cycle_index + 1) % len(items)
            last_cycle = current_time
            _LOGGER.info(
                f"Cycling to image {cycle_index + 1}/{len(items)}: {items[cycle_index].path}"
            )

        # Ensure index is valid
        if items:
            cycle_index = cycle_index % len(items)
            current_path = items[cycle_index].path
        else:
            current_path = None

        return {
            "images": items,
            "count": len(items),
            "total_count": last_total_count,
            "current_path": current_path,
            "cycle_index": cycle_index,
        }

    # Coordinator update frequency should be frequent enough to handle cycling,
    # while respecting the configured refresh interval.
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{entry.entry_id}",
        update_method=async_update_data,
        update_interval=timedelta(seconds=cycle_interval),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "coordinator": coordinator,
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
