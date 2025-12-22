# Changelog

## 0.1.5 - 2025-12-23

- CI: Added GitHub Actions workflow to run `pre-commit` with `uv` on PRs targeting `main`; added concurrency to cancel superseded runs and avoid duplicates.
- Tooling: Switched local pre-commit hooks to `uv run` for consistent tool versions; added `ruff format` hook; included `pre-commit` in `dev` extras.
- HA image entity: Aligned `SlideshowImageEntity` with HA semantics (typed async reads, removed manual state writes, rely on `image_last_updated`).

## 0.1.4 - 2025-12-22

- Initial release for HACS testing and feedback
- This is still a vibe-coded project; treat it as experimental and untrusted until further hardening
- Core slideshow helper integration packaged for early adopters
