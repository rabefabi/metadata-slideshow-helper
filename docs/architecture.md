# Technical Architecture
- Custom integration `slideshow_helper`; platforms: sensor (current image/count) and image entity.
- Coordinator pattern: `DataUpdateCoordinator` cycles images on a timer; state includes `current_path`, `current_url`, `cycle_index`, `images`.
- Media scanning: `MediaScanner` walks configured directory, reads metadata (EXIF/ratings), filters by rating/tags.
- Services: helper service to fetch filtered image URLs/metadata.
- Config flow: options for media_dir, min_rating, include_tags, exclude_tags, cycle_interval, refresh_interval.

## Runtime Notes & Learnings
- Use `ImageEntity` refresh semantics: bump `image_last_updated` when the coordinator advances to a new `current_path`. The frontend refetches bytes upon this timestamp change.
- Coordinator checks every second but only advances when `cycle_interval` elapses; sensors and the image entity mirror coordinator state.
- Image entity seeds `access_tokens` and keeps `_attr_should_poll = False`; bytes are read via executor to avoid blocking the event loop.

### Recent Fix: Frontend Refresh
- Image entity state now mirrors `image_last_updated` (ISO timestamp). This makes `last_changed` advance each cycle, ensuring Picture Entity cards refresh reliably.
- `image_url` returns `None`; Lovelace fetches bytes via `async_image()` instead of a static URL.

## Decision: Entity-Driven Refresh
- Coordinator owns slideshow cadence and sets `current_path`.
- Image entity implements `async_image()` to serve bytes for `current_path` and updates `image_last_updated` on each change.
- Sensors continue exposing `current_url`/`current_path` and `cycle_index` for debugging or auxiliary UI.
