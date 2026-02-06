# Metadata Slideshow Helper

> [!WARNING]
> WIP Vibe Coding Project and my first Home Assistant Integration - I wouldn't trust this yet.
> If you want to try it out nonetheless, click below:  
> [![Open your Home Assistant instance and open this repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=rabefabi&repository=metadata-slideshow-helper&category=integration)

## Configuration Notes

- `media_dir`: One or more directories to scan for images. For multiple directories, separate paths with commas (e.g., `/media/photos/2020,/media/photos/2021`). All directories will be scanned and their images combined into one slideshow.
- `min_rating`: Minimum XMP/EXIF rating to include (0–5 scale).
- `include_tags` / `exclude_tags`: Tag filters applied to image metadata (case-insensitive).
- `advance_interval` (seconds): Time between advancing to the next matching image.
- `rescan_interval` (seconds): Time between rescanning the media directory for new/changed files.
  - Must be greater than `advance_interval`.
  - The coordinator updates entities every `advance_interval`, but only rescans the filesystem every `rescan_interval` to reduce I/O.
- `advance_mode`: Image advancement mode (`sequential` or `smart_random`).
  - `sequential`: Always advance to the next image in order (default).
  - `smart_random`: Advance sequentially for N images, then jump to a random position.
    - `smart_random_sequence_length`: For smart random mode, number of images to advance sequentially before jumping (default 3). Only used when `advance_mode` is `smart_random`.

## Entities

- **Slideshow** (image): Shows current image; updates when advancing to the next match
- **Matching Image Count** (sensor, Diagnostic): State is count of images passing all filters
- **Discovered Image Count** (sensor, Diagnostic): Total image files found in media directory
- **Failed Image Count** (sensor, Diagnostic): Image files that couldn't be read or have corrupted metadata
- **Non-Image File Count** (sensor, Diagnostic): Non-image files encountered during scan

## Terminology

| Term | Definition |
|------|-----------|
| **Discovered images** | All image files found in the media directory during a rescan. |
| **Matching images** | Images from the discovered set that pass all configured filters (min_rating, include_tags, exclude_tags). |
| **Rescan** | Walking the media directory and reading image metadata; controlled by `rescan_interval`. |
| **Advance** | Automatically moving to the next matching image; happens every `advance_interval` seconds. |
