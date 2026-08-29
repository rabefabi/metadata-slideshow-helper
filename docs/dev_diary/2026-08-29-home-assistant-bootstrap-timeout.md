# 2026-08-29: Home Assistant bootstrap timeout during initial setup

## Problem summary

Issue #20 reports that the integration stops loading after a Home Assistant upgrade. The log shows that setup is cancelled during the first data refresh: [Issue #20](https://github.com/rabefabi/metadata-slideshow-helper/issues/20), [Home Assistant config entry setup flow](https://developers.home-assistant.io/docs/config_entries_index/), and [Home Assistant coordinator refresh implementation](https://github.com/home-assistant/core/blob/dev/homeassistant/helpers/update_coordinator.py).

- `async_setup_entry()` calls `coordinator.async_config_entry_first_refresh()` and Home Assistant treats that as part of the bootstrap path: [Home Assistant coordinator source](https://github.com/home-assistant/core/blob/dev/homeassistant/helpers/update_coordinator.py#L332-L367).
- the coordinator invokes `SlideshowCoordinator.async_update_data()` during the first refresh: [Home Assistant coordinator source](https://github.com/home-assistant/core/blob/dev/homeassistant/helpers/update_coordinator.py#L332-L367).
- that method calls `self.hass.async_add_executor_job(self.scanner.scan_and_filter)` while the config entry is still in setup: [Home Assistant config entries source](https://github.com/home-assistant/core/blob/dev/homeassistant/config_entries.py#L760-L830).
- the task is cancelled with `asyncio.exceptions.CancelledError: Global task timeout: Bootstrap stage 2 timeout`: [Home Assistant config entries source](https://github.com/home-assistant/core/blob/dev/homeassistant/config_entries.py#L760-L830).

This is a startup-time problem, not a YAML or config-flow validation problem, because the integration is doing expensive filesystem work inside the bootstrap path: [Home Assistant config entries source](https://github.com/home-assistant/core/blob/dev/homeassistant/config_entries.py#L760-L830), [Home Assistant coordinator source](https://github.com/home-assistant/core/blob/dev/homeassistant/helpers/update_coordinator.py#L332-L367).

## Root cause

The scanner was walking each configured media root multiple times: [Home Assistant coordinator guidance](https://developers.home-assistant.io/blog/2024-08-05-coordinator_async_setup/), [Home Assistant config-entry docs](https://developers.home-assistant.io/docs/config_entries_index/).

- once for `*.jpg`
- once for `*.jpeg`
- once for `*.png`
- plus an additional pass to count non-image files

This pattern is extremely expensive on a large library and can exceed Home Assistant's bootstrap tolerance during the initial setup refresh: [Home Assistant coordinator source](https://github.com/home-assistant/core/blob/dev/homeassistant/helpers/update_coordinator.py#L332-L367), [Home Assistant config entries source](https://github.com/home-assistant/core/blob/dev/homeassistant/config_entries.py#L760-L830).

## What changed

The implementation now follows the safer Home Assistant pattern: the integration keeps startup lightweight and defers the first full media scan to a background task after the entry has finished setting up: [Home Assistant config-entry docs](https://developers.home-assistant.io/docs/config_entries_index/), [Home Assistant coordinator setup blog](https://developers.home-assistant.io/blog/2024-08-05-coordinator_async_setup/).

At the same time, the scanner still avoids the worst startup cost by walking each root only once and filtering as it goes: [Home Assistant coordinator source](https://github.com/home-assistant/core/blob/dev/homeassistant/helpers/update_coordinator.py#L332-L367), [Home Assistant config entries source](https://github.com/home-assistant/core/blob/dev/homeassistant/config_entries.py#L760-L830).

- valid images are collected immediately
- unsupported file extensions are counted as non-image files
- unreadable files are counted as failed files
- metadata is still read per image as before

This keeps `async_setup_entry()` fast while using the existing periodic rescan behavior as the normal post-startup refresh mechanism: [Home Assistant async refresh scheduling source](https://github.com/home-assistant/core/blob/dev/homeassistant/helpers/update_coordinator.py#L245-L311).

## Best-practice recommendation for long-running startup work

Current Home Assistant guidance favors a lightweight setup path and moving heavy work off the bootstrap critical path: [Home Assistant config-entry docs](https://developers.home-assistant.io/docs/config_entries_index/), [Home Assistant coordinator setup blog](https://developers.home-assistant.io/blog/2024-08-05-coordinator_async_setup/).

The integration now follows that pattern by treating the full media scan as a deferred background refresh instead of a required part of startup: [Home Assistant coordinator source](https://github.com/home-assistant/core/blob/dev/homeassistant/helpers/update_coordinator.py#L332-L367), [Home Assistant config entries source](https://github.com/home-assistant/core/blob/dev/homeassistant/config_entries.py#L760-L830).

This is safer than relying only on a faster scan because very large media libraries can still exceed the bootstrap budget even with a single-pass walk: [Home Assistant config entries source](https://github.com/home-assistant/core/blob/dev/homeassistant/config_entries.py#L760-L830), [Home Assistant developer docs](https://developers.home-assistant.io/docs/config_entries_index/).

## Verification status

The relevant test file passes after the startup-safe change: [project test file](../../tests/test_metadata_slideshow_helper.py), [project changelog](../../CHANGELOG.md).

This means the code is in a good state for live verification on a real Home Assistant instance, where the actual media-library size will determine whether the deferred background scan is sufficient for the local environment: [Home Assistant config-entry docs](https://developers.home-assistant.io/docs/config_entries_index/), [Home Assistant coordinator source](https://github.com/home-assistant/core/blob/dev/homeassistant/helpers/update_coordinator.py#L332-L367).
