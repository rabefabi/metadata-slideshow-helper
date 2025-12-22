# Agent Operating Guide

- Add comments only when helpful for non-obvious logic.
- Tooling: use `ruff` for linting/imports,`mypy` with `homeassistant-stubs` if type checks needed.
- After edits that affect HA, restart the container and check logs for errors.
  - If necessary, verify the UI via the Playwright MCP server
- Document major decisions in `docs/` and keep responses concise with required link formatting.
- When proposing steps or actions, make sure they are numerated, so that it's easier to respond
- Bumping versions: Make sure that the versions are consistent across `pyproject.toml` and `custom_components/<component>/manifest.json`
