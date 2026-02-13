# Developer Setup and Conventions

- **Dependency and tooling runner:** Use `uv` for all local dev tasks.
  - Create venv: `uv venv .venv --python 3.13`
  - Install app + dev deps from `pyproject.toml`: `uv sync --extra dev`
  - Static checks (lint, types, formatting): `uv run pre-commit run --all-files`
  - Pre-commit install: `uv run pre-commit install`

## DevContainer Setup

This repository includes a DevContainer configuration for consistent local development environments.

**Prerequisites:**
- [Visual Studio Code](https://code.visualstudio.com/)
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- Docker

**Quick Start:**
1. Open this repository in VS Code
2. Command Palette: `Dev Containers: Reopen in Container`
3. Wait for build (1-2 minutes first run) - automatically installs all dependencies via `uv sync --all-extras`
4. Home Assistant config template is automatically copied from `.devcontainer/configuration.yaml` to `.haconfig/configuration.yaml`

### Manual Integration Testing with Home Assistant

After DevContainer opens, you have two options for starting Home Assistant:

#### Option 1: Automated Headless Setup (Recommended for quick testing)

1. **Via VS Code Task:**
   - Command Palette: `Tasks: Run Task → Initialize Home Assistant (Headless)`

2. The `init-headless` script automates the complete setup:
   - Resets Home Assistant configuration
   - Generates sample media for testing
   - Creates admin user (username: `admin`, password: `dev-password`)
   - Starts Home Assistant in debug mode on `http://localhost:8123`

3. Access Home Assistant and log in with the admin credentials

#### Option 2: Manual Setup

1. **Via VS Code Task:**
   - Command Palette: `Tasks: Run Task → Run Home Assistant`

2. Home Assistant starts in debug mode on `http://localhost:8123`

3. First run: Complete HA onboarding, create test user, add integration to dashboard

4. **Config directory management:**
   - Source: `.devcontainer/configuration.yaml` (committed to repository)
   - Runtime: Copied to `.haconfig/configuration.yaml` during DevContainer initialization
   - `.haconfig/` is ephemeral and git-ignored; the source of truth is `.devcontainer/configuration.yaml`
   - To modify config: Edit `.devcontainer/configuration.yaml` and commit changes

5. **Stop Home Assistant:** Click stop button in VS Code or `Ctrl+C` in task terminal

The DevContainer includes Home Assistant as a Python package, so you can test the integration directly without separate containers.

### Unit Testing

Run tests without starting Home Assistant:

```bash
uv run pytest
```

This matches CI/CD approach—no runtime HA instance needed for automated tests.

## Known Limitations

### Onboarding UI Still Appears

When using the "Initialize Home Assistant (Headless)" task, the onboarding UI may still appear despite the automated setup. This is expected behavior and can be safely skipped by clicking through or closing the dialog. The admin user credentials (`admin` / `dev-password`) work regardless of the onboarding UI appearance.

The `init-headless` script attempts to mark onboarding as complete by updating the storage file, but Home Assistant's onboarding logic is not fully suppressed yet. See the TODO comment in the [scripts/init-headless](../scripts/init-headless) script for future improvements.
