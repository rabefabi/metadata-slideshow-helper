# 2025-12-22 Project Cleanup and Tooling Enhancements

Goals:

- Add local static code checks
- Add CI
- Solve issues identified by static checks

## Dev Diary

- Added `pre-commit` with local hooks to run `ruff` and `mypy` on all files.
  - The local hooks ensure that the same tool version is used in all cases (CI, local dev, etc).
  - Hooks are executed via `uv run` so editors/CI that lack direct `ruff`/`mypy` on PATH still use the project venv.
- Added GitHub Actions CI workflow to run the same static checks on all PRs.
  - CI triggers and deduplication: configured the workflow to run on `pull_request` targeting `main` and `push` to `main` only, preventing duplicate executions that happen when both `push` and `pull_request` fire for PR branches.
  - Added `concurrency` with a ref-based group to cancel in-progress runs when new commits land, keeping CI fast and reducing noise. See workflow at [.github/workflows/pre-commit.yaml](.github/workflows/pre-commit.yaml).
- Fixed `SlideshowImageEntity` to align with Home Assistant image semantics: imports moved to top-level for linting, async image reads typed, and we stopped writing `_attr_state` so we rely solely on `image_last_updated` for cache-busting refreshes (per HA image entity guidance: <https://developers.home-assistant.io/docs/core/entity/image/#cache-busting-and-updates>).
