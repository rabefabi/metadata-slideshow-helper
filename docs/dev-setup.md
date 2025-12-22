# Developer Setup and Conventions

- **Python Version:** Target Python 3.13 across tooling.
  - `pyproject.toml` declares `requires-python >=3.13` under `[project]`.
  - `mypy` is configured with `python_version = "3.13"`.

- **Dependency and tooling runner:** Use `uv` for all local dev tasks.
  - Create venv: `uv venv .venv --python 3.13`
  - Install app + dev deps from `pyproject.toml`: `uv sync --extra dev`
  - Lint (with autofix): `uv run ruff check --fix`
  - Types: `uv run mypy custom_components/slideshow_helper`

- **Ruff configuration:** Import ordering and other lint rules are enforced via the built-in sorter; no separate `isort` config is needed.

- **Type and entity expectations (Home Assistant stubs):**
  - Avoid `JsonValueType`; simple primitives (ints/strings) work best for service responses and state attributes.
  - Annotate mutable class attributes with `ClassVar` (e.g., in `SlideshowImageEntity`).
  - Image entity state is the cache-busted URL so HA sees changes.

- **Coordinator behavior:**
  - Cycling logic runs in the coordinator. Sensors and image entity expose `current_url`/`current_path` only.
  - Guard scanning when `media_dir` is missing to avoid runtime errors.
  - Cache-buster query param (`?v=<cycle_index>`) is required to force Lovelace refreshes.

- **Home Assistant runtime:**
  - Use the provided `docker-compose.yml`. Mounts:
    - `/config` → `ha-config/`
    - `/config/custom_components` (read-only) → `custom_components/`
    - `/media` (read-only) → `sample-media/`
  - Prefer `media-source://media_source/local/...` URLs in dashboards; direct `/media/...` works with mounted paths.

- **Troubleshooting frontend refresh:**
  - Picture cards can cache images even with cache-busting; the card may show `Unknown` and not auto-advance. Browser refresh or switching card type can help; the backend still cycles correctly.

- **Quick commands**

  ```bash
  uv venv .venv --python 3.13
  uv sync --extra dev
  uv run ruff check && uv run mypy custom_components/slideshow_helper
  docker compose up -d && docker compose logs -f homeassistant
  ```

### Lovelace usage

- Prefer a Picture Entity card bound to `image.slideshow_helper`.
- The image entity refreshes when `image_last_updated` changes; state now mirrors the timestamp so `last_changed` advances each cycle.
