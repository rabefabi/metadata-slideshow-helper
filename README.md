# Metadata Slideshow Helper

WIP Vibe Coding Project - I wouldn't trust this yet.

## Configuration Notes

- `media_dir`: Directory to scan for images.
- `min_rating`: Minimum XMP/EXIF rating to include.
- `include_tags` / `exclude_tags`: Tag filters applied to image metadata.
- `cycle_interval` (seconds): Time between image changes.
- `refresh_interval` (seconds): Filesystem rescan cadence and coordinator update frequency.
  - Must be greater than `cycle_interval`.
  - Acts as a lower bound: effective rescan occurs when the next cycle is due, not earlier.

## Entities

- Slideshow Image (image): Shows current image; updates when cycling
- Slideshow Image Count (sensor, Diagnostic): State is filtered count; attributes include `filtered_image_count` and `total_image_count`
- Slideshow Status (sensor, Diagnostic): State is `active`/`empty`; attributes include `current_path`, `cycle_index`, `filtered_image_count`, `total_image_count`
