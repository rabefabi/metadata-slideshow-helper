# Agent Operating Guide

## Coding & Tooling Style

- You have access to the latest documentation via the Context7 MCP plugin - use it to look up the current state of the art for all libraries and frameworks. 
- Add comments only when helpful for non-obvious logic.
- Use the editor linting and formatting tools
- Tooling: use `ruff` for linting/imports,`mypy` with `homeassistant-stubs` if type checks needed.
- After edits that affect HA, restart the container and check logs for errors.
  - If necessary, verify the UI via the Playwright MCP server

## Documentation

- Document major decisions in `docs/` and keep responses concise with required link formatting.

## User Interaction

- When proposing steps or actions, make sure they are numerated, so that it's easier to respond

## Git Commits, Versioning & Releases

- For git commits, use conventional commit messages
  - Updates for the coding agent config should use the `build(agents):` prefix
- Bumping versions: Make sure that the versions are consistent across `pyproject.toml` and `custom_components/<component>/manifest.json`
  - When creating git tags, don't prefix with `v`, just use the version number directly, e.g. `0.1.0`
