"""Slideshow Helper integration."""
from __future__ import annotations

import logging
import os
import time
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import helper as _helper
from .const import (
    CONF_CYCLE_INTERVAL,
    CONF_MEDIA_DIR,
    CONF_REFRESH_INTERVAL,
    DEFAULT_CYCLE_INTERVAL,
    DEFAULT_REFRESH_INTERVAL,
    DOMAIN,
    INTEGRATION_VERSION,
)
from .http import SlideshowImageView
from .scanner import MediaScanner

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor", "image"]

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.info("slideshow_helper version %s starting", INTEGRATION_VERSION)

    # Register HTTP view for serving images (once per domain)
    if "http_view_registered" not in hass.data[DOMAIN]:
        hass.http.register_view(SlideshowImageView())
        hass.data[DOMAIN]["http_view_registered"] = True

    # Create coordinator that scans media directory
    media_dir = entry.data.get(CONF_MEDIA_DIR)
    # Note: refresh_interval currently not used by coordinator
    _ = entry.data.get(
        CONF_REFRESH_INTERVAL,
        entry.options.get(CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL),
    )
    cycle_interval = entry.data.get(CONF_CYCLE_INTERVAL, entry.options.get(CONF_CYCLE_INTERVAL, DEFAULT_CYCLE_INTERVAL))

    # Cycling state
    cycle_index: int = 0
    last_cycle: float = time.time()
    cached_items: list = []
    last_scan: float = 0.0
    scan_interval: float = 300.0  # Rescan filesystem every 5 minutes

    async def async_update_data():
        """Fetch data from media scanner and handle cycling."""
        nonlocal last_cycle, cycle_index, cached_items, last_scan
        
        current_time = time.time()
        
        # Only rescan filesystem periodically, not every update
        if not media_dir:
            items = []
        elif not cached_items or (current_time - last_scan) >= scan_interval:
            _LOGGER.info(f"Scanning media_dir: {media_dir}")
            scanner = MediaScanner(media_dir)
            items = await hass.async_add_executor_job(scanner.scan)
            cached_items = items
            last_scan = current_time
            if items:
                _LOGGER.info(f"Found {len(items)} images")
            else:
                _LOGGER.warning(f"No images found in {media_dir}")
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
            relative_path = os.path.relpath(current_path, media_dir)
            # Encode path and use custom view URL
            encoded_path = relative_path.replace("/", "_SLASH_")
            # Add cache-buster so Lovelace cards refresh when cycling
            current_url = f"/api/slideshow_helper/{entry.entry_id}/{encoded_path}?v={cycle_index}"
        else:
            current_path = None
            current_url = None

        return {
            "images": items,
            "count": len(items),
            "current_path": current_path,
            "current_url": current_url,
            "cycle_index": cycle_index,
        }

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{entry.entry_id}",
        update_method=async_update_data,
        update_interval=timedelta(seconds=1),  # Check every second for cycling
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "coordinator": coordinator,
    }

    # Register services on first setup
    await _helper.async_register_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
