# 2025-12-22 Project Cleanup and Tooling Enhancements

Goals:

- Add local static code checks
- Add CI
- Solve issues identified by static checks

## Dev Diary

- Added `pre-commit` with local hooks to run `ruff` and `mypy` on all files.
  - The local hooks ensure that the same tool version is used in all cases (CI, local dev, etc).
- Added GitHub Actions CI workflow to run the same static checks on all PRs.
- Fixed `SlideshowImageEntity` to align with Home Assistant image semantics: imports moved to top-level for linting, async image reads typed, and we stopped writing `_attr_state` so we rely solely on `image_last_updated` for cache-busting refreshes (per HA image entity guidance: <https://developers.home-assistant.io/docs/core/entity/image/#cache-busting-and-updates>).
