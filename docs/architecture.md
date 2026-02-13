# Technical Architecture

- Custom integration `metadata_slideshow_helper`; platforms: sensor (current image/count) and image entity.
- Coordinator pattern: `DataUpdateCoordinator` advances to next image on a timer; state includes `current_path`, `current_url`, `cycle_index`, `matching_images`, `discovered_images`.
- Media scanning: `MediaScanner` walks configured directory, reads metadata (EXIF/ratings), filters by rating/tags.
- Config flow: options for media_dir, min_rating, include_tags, exclude_tags, advance_interval, rescan_interval.

## Configuration Methods

The integration supports both UI and YAML configuration:

- **UI Config Flow**: Standard Home Assistant integration setup through Settings → Devices & services
- **YAML Import Flow**: Automatically imports configuration from `configuration.yaml` on startup
  - YAML config is stored in `entry.options` (not `entry.data`) to maintain consistency with the options flow
  - After import, the integration behaves identically to UI-configured instances
  - Changes to YAML require integration reload to take effect

## Runtime Notes & Learnings

- Use `ImageEntity` refresh semantics: bump `image_last_updated` when the coordinator advances to a new `current_path`. The frontend refetches bytes upon this timestamp change.
- Coordinator updates on the minimum of `advance_interval` and `rescan_interval` (bounded to ≥1s) and only advances when `advance_interval` elapses; sensors and the image entity mirror coordinator state.
- Filesystem rescan uses `rescan_interval`; scanning is skipped between rescans to reduce I/O.
- Validation: `rescan_interval` must be greater than `advance_interval`. The rescan interval acts as a lower bound: effective rescan happens no sooner than the next advance due.
- Image entity keeps `_attr_should_poll = False`; bytes are read via executor to avoid blocking the event loop.

### Recent Fix: Frontend Refresh

- Image entity state now mirrors `image_last_updated` (ISO timestamp). This makes `last_changed` advance each cycle, ensuring Picture Entity cards refresh reliably.
