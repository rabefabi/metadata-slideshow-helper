# Developer Setup and Conventions

- **Dependency and tooling runner:** Use `uv` for all local dev tasks.
  - Create venv: `uv venv .venv --python 3.13`
  - Install app + dev deps from `pyproject.toml`: `uv sync --extra dev`
  - Static checks (lint, types, formatting): `uv run pre-commit run --all-files`
  - Pre-commit install: `uv run pre-commit install`

- **Quick commands**

  ```bash
  uv venv .venv --python 3.13
  uv sync --extra dev
  uv run ruff check && uv run mypy custom_components/slideshow_helper
  docker compose up -d && docker compose logs -f homeassistant
  ```

## Home Assistant development runtime

- Use the provided `docker-compose.yml`. It launches a home assistant deployment with the integration already installed, and the `sample_media` already mounted
- Manually create a test user and test home configuration, and add the `slideshow_helper` integration to the default dashboard,
 so that the coding agent can access it via e.g. the playwright MCP server.
