# Changelog

## Unreleased

## 0.2.1 - 2026-01-30

### Improvements
- Media Scanner: Allowed multiple directories in `media_dir` configuration (comma-separated); scans combined into single slideshow

## 0.2.0 - 2026-01-30

### Breaking Changes
- **Renamed domain**: `slideshow_helper` → `metadata_slideshow_helper` (requires reconfiguration)
- **Config schema version bump**: v1 → v2 (configuration entries need migration)
- **Configuration keys renamed**:
  - `cycle_interval` → `advance_interval` (time between advancing to next image)

### Features
- Config validation: `refresh_interval` must be > `advance_interval` with clear error messaging
- Reconfigure support: Update integration settings without removing/re-adding
- Improved terminology: Consistent use of "discovered images" (all scanned) vs "matching images" (after filters)
- Better logging: Clear distinction between rescanning filesystem and advancing images

### Improvements
- Sensor attributes: Renamed to `matching_image_count` and `discovered_image_count` for clarity
- Image Count sensor: Marked as Diagnostic category
- Scanner: Switched to `pathlib` for filesystem operations; improved error handling
- Constants: Eliminated magic strings by using explicit `DATA_*` constants throughout
- Documentation: Added terminology table to README defining key concepts

### Removals
- Removed unused entities: `SlideshowCurrentImageSensor`, `SlideshowInfoSensor`
- Removed deprecated services: `get_image_urls` and custom HTTP views
- Removed unused runtime dependency: `exif` package
- Removed options flow (use reconfigure instead)

### Fixes
- Fixed uninitialized `last_discovered_count` variable
- CI: Added test dependencies to pre-commit workflow

## 0.1.6 - 2025-12-28

- Feat: Add XMP tag filtering support with comprehensive metadata handling
- Fix: Actually read configuration from Home Assistant
- Fix: Reduce dependencies, order them properly
- Tests: Add integration tests for image filtering by rating and tags
- Tests: Add fixtures to generate test images
- Chore: Fix ruff linting warnings
- Build: Add learnings regarding dependencies and error handling

## 0.1.5 - 2025-12-23

- CI: Added GitHub Actions workflow to run `pre-commit` with `uv` on PRs targeting `main`; added concurrency to cancel superseded runs and avoid duplicates.
- Tooling: Switched local pre-commit hooks to `uv run` for consistent tool versions; added `ruff format` hook; included `pre-commit` in `dev` extras.
- HA image entity: Aligned `SlideshowImageEntity` with HA semantics (typed async reads, removed manual state writes, rely on `image_last_updated`).

## 0.1.4 - 2025-12-22

- Initial release for HACS testing and feedback
- This is still a vibe-coded project; treat it as experimental and untrusted until further hardening
- Core slideshow helper integration packaged for early adopters
