# Technical Architecture

- Custom integration `metadata_slideshow_helper`; platforms: sensor (current image/count) and image entity.
- Coordinator pattern: `DataUpdateCoordinator` cycles images on a timer; state includes `current_path`, `current_url`, `cycle_index`, `images`.
- Media scanning: `MediaScanner` walks configured directory, reads metadata (EXIF/ratings), filters by rating/tags.
- Config flow: options for media_dir, min_rating, include_tags, exclude_tags, cycle_interval, refresh_interval.

## Runtime Notes & Learnings

- Use `ImageEntity` refresh semantics: bump `image_last_updated` when the coordinator advances to a new `current_path`. The frontend refetches bytes upon this timestamp change.
- Coordinator updates on the minimum of `cycle_interval` and `refresh_interval` (bounded to ≥1s) and only advances when `cycle_interval` elapses; sensors and the image entity mirror coordinator state.
- Filesystem rescan uses `refresh_interval`; scanning is skipped between rescans to reduce I/O.
- Validation: `refresh_interval` must be greater than `cycle_interval`. The refresh interval acts as a lower bound: effective rescan happens no sooner than the next cycle due.
- Filesystem rescan uses `refresh_interval`; scanning is skipped between rescans to reduce I/O.
- Image entity keeps `_attr_should_poll = False`; bytes are read via executor to avoid blocking the event loop.

### Recent Fix: Frontend Refresh

- Image entity state now mirrors `image_last_updated` (ISO timestamp). This makes `last_changed` advance each cycle, ensuring Picture Entity cards refresh reliably.
