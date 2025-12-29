# Changelog

## Unreleased

- Entities: Image count marked as Diagnostic; added Slideshow Status sensor with attributes
- Attributes: Expose `filtered_image_count` and `total_image_count` for quick filter visibility
- Cleanup: Removed unused `exif` runtime dependency from manifest

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
