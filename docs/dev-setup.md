# Developer Setup and Conventions

- **Dependency and tooling runner:** Use `uv` for all local dev tasks.
  - Create venv: `uv venv .venv --python 3.13`
  - Install app + dev deps from `pyproject.toml`: `uv sync --extra dev`
  - Lint (with autofix): `uv run ruff check --fix`
  - Types: `uv run mypy custom_components/slideshow_helper`
- **Ruff configuration:** Import ordering and other lint rules are enforced via the built-in sorter; no separate `isort` config is needed.
- **Home Assistant development runtime:**
  - Use the provided `docker-compose.yml`. It launches a home assistant deployment with the integration already installed, and the `sample_media` already mounted

- **Quick commands**

  ```bash
  uv venv .venv --python 3.13
  uv sync --extra dev
  uv run ruff check && uv run mypy custom_components/slideshow_helper
  docker compose up -d && docker compose logs -f homeassistant
  ```
