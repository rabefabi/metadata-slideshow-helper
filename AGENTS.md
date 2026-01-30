# Agent Operating Guide

## Coding & Tooling Style

- You have access to the latest documentation via the Context7 MCP plugin - use it to look up the current state of the art for all libraries and frameworks.
- Add comments only when helpful for non-obvious logic.
- For dependency management use `uv sync`, never use `uv pip`.
- **Home Assistant dependencies**: Keep `pyproject.toml` (dev/test) and `custom_components/<component>/manifest.json` (runtime) in sync. Any runtime dependency for the integration must be declared in `manifest.json` under `requirements`.
- Use the editor linting and formatting tools.
- Tooling: `uv run pre-commit run --all-files` to run all pre-commit checks and pytest tests locally. This will also handle formatting for you.
- After edits that affect Home Assistant or after larger changes, (re)start the home assistant container via the `docker-compose.yml` and check logs for errors.
  - If necessary, verify the UI via the Playwright MCP server
- **Error handling**: Use `contextlib.suppress(ValueError)` instead of try-except-pass blocks for handling specific exceptions. This is more concise and linter-friendly.
- **Library functions over utilities**: Prefer using built-in or library functions (e.g., Pillow's `getxmp()`) over writing custom parsing/extraction utilities. Only create helpers when no library function covers the use case.
- **YAGNI principle**: Implement only what is needed for the current use case. Avoid speculative features, fallbacks, or abstractions that aren't yet required. Revisit when actual requirements emerge.

## Documentation

- Document major decisions in `docs/` and keep responses concise with required link formatting.

## Human Interaction

- Use a direct communication style, don't use words like "powerful", "comprehensive" etc.
- When proposing steps or actions, make sure they are numerated, so that it's easier to respond

## Git Commits, Versioning & Releases

- Do not git stage or commit code without explicit instruction to do so
- For git commits, use conventional commit messages
  - Updates for the coding agent config should use the `build(agents):` prefix
- Bumping versions: Make sure that the versions are consistent across `pyproject.toml` and `custom_components/<component>/manifest.json`
  - When creating git tags, don't prefix with `v`, just use the version number directly, e.g. `0.1.0`
- Version Numbers: We're not quite following semantic versioning, but:
  - Increment patch version for bug fixes and minor improvements
  - Increment minor version for new features and breaking changes
- Remember to maintain the `CHANGELOG.md`, keep a log of unreleased changes at the top
