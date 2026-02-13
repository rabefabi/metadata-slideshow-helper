# DevContainer Setup Implementation - Issue #16

**Date:** February 13, 2026

## Issue Reference

[GitHub Issue #16: Add Devcontainer setup](https://github.com/rabefabi/metadata-slideshow-helper/issues/16)

### Acceptance Criteria
- ✅ Researched best practices for DevContainers in Home Assistant Integration Repositories
- ✅ Documented & Implemented these best practices

## Research Findings

### Home Assistant Ecosystem Standard
Established HACS integrations (`better_thermostat`, `hacs_waste_collection_schedule`) and official HA documentation recommend DevContainers as the primary development approach—not docker-compose orchestration.

### Key Discovery: Testing Strategy Separation
- **CI/CD (GitHub Actions):** Unit tests + linting only—no Home Assistant runtime
- **Local development:** DevContainer with optional Home Assistant runtime for manual integration testing

This means developers can test code locally without the overhead of docker-compose, while CI remains fast and deterministic.

## Decisions Made

### 1. Why Replace docker-compose with DevContainer + Home Assistant Package?
- **Simpler for developers:** One container, not two. One click to open ("Reopen in Container").
- **Lighter weight:** No need to orchestrate separate containers. Home Assistant runs as a Python package.
- **Better debugging:** VS Code integration with DevContainers supports F5 debugging directly into Home Assistant.
- **Industry standard:** `better_thermostat` (established integration) uses this exact pattern.
- **Explicit control:** Developers opt-in to start Home Assistant manually (via Task), not always running.

### 2. Why Home Assistant as Dev Dependency in pyproject.toml?
- Single source of truth for all dependencies (both tools and runtime).
- `uv sync --all-extras` installs everything once in DevContainer—developers don't need separate setup steps.
- Follows repository convention of using `uv` as the universal dependency manager.

### 3. Why Ephemeral .haconfig/ Directory?
- Source of truth: `.devcontainer/configuration.yaml` (committed to repository)
- Runtime copy: `.haconfig/configuration.yaml` (auto-generated during DevContainer init, git-ignored)
- `.haconfig/` also contains Home Assistant's runtime data (database, secrets, cache)—ephemeral, never committed.
- Auto-regenerated each checkout from source—ensures clean state and consistent setup across developers.
- Any configuration changes belong in `.devcontainer/configuration.yaml` and should be committed.

### 4. Custom Dockerfile for Full Tool Control
Rather than relying solely on the base Python devcontainer image, we created a custom `.devcontainer/Dockerfile` that extends it to include:
- **Node.js + npm** — For MCP server development and execution
- **uv** — Pre-installed for immediate use in `postCreateCommand`
- **UV_LINK_MODE=copy** — Set to avoid warnings about hard links on different filesystems when mounting volumes (per [official uv Docker guide](https://docs.astral.sh/uv/guides/integration/docker/#caching))

Added `.dockerignore` to exclude build artifacts (`.venv`, `__pycache__`, etc.) and directories that are runtime-mounted (`.git`, `.haconfig`) following [official best practices](https://docs.astral.sh/uv/guides/integration/docker/#installing-a-project). DevContainers mount the workspace at runtime, so `.git` is available inside the container without being copied into the Docker image during build.

This approach provides:
- **Predictable environment** — All developers get the exact same toolset
- **Explicit dependencies** — Easy to see which development tools are needed
- **Clean builds** — Platform-specific virtual environments aren't included in image builds
- **Easy to extend** — Adding new tools is straightforward

### 5. Future: CI/CD Alignment Gap
Current state: GitHub Actions uses `astral-sh/setup-uv@v7` with Python 3.13, while DevContainer uses a custom image based on `mcr.microsoft.com/devcontainers/python:3.13-bookworm`. These run slightly different base environments.

Should consider aligning these for maximum parity—either both using the same Docker image or both using minimal Python installations. Deferred for future improvement.

## Headless Home Assistant Setup for Development

### Why Headless Setup?
Developers benefit from a completely automated, reproducible setup that doesn't require manual UI configuration. This:
- **Speeds up iteration:** Fresh start takes seconds, not minutes of clicking through onboarding
- **Enables CI/CD-like testing locally:** Same setup every time, no drift between developer environments
- **Supports unattended testing:** Crucial for integration testing and automated local workflows
- **Documents configuration as code:** All settings committed to repo instead of buried in UI state

### Configuration Source-of-Truth
Chose `.devcontainer/` folder as single source of truth for development environment:
- **Templates committed to repo** (`configuration.yaml`, `secrets.yaml.template`, etc.)
- **Each developer has their copy** (`.haconfig/` auto-generated, git-ignored)
- **Separation of concerns:** Configuration templates vs. runtime state vs. secrets

### Known Limitation: Onboarding UI Still Appears
Current implementation marks onboarding steps as complete in storage, but Home Assistant still shows onboarding UI on first login. Why we're living with this:
- **Low priority for development:** Real blocker would be if setup failed; UI inconvenience is acceptable
- **Root cause unclear:** Home Assistant's onboarding detection logic is complex; may require diving into HA source or API changes
- **Good enough for now:** Developers can skip through onboarding manually (few clicks) or investigate proper fix later
- **Documented with TODO:** Future maintainers will immediately see this is incomplete

Proper fix would likely involve:
- Deep-diving into Home Assistant's `onboarding` component code
- Finding how HA determines when onboarding is truly "done"
- Possibly using a different API endpoint or triggering full onboarding completion differently
- Or: wait for proper Home Assistant headless mode/flag (if it exists in newer versions)

## Integration Pre-Configuration for Development

### Why YAML Configuration Instead of Storage Manipulation?
Initial approach attempted to write directly to Home Assistant's storage files (`core.config_entries`) to pre-configure the integration. This was abandoned for YAML configuration because:
- **Respects Home Assistant conventions:** YAML is the documented, supported way for configuration-as-code
- **Avoids internal API coupling:** Storage file format is internal implementation detail, subject to change
- **Maintains data integrity:** Home Assistant manages storage file lifecycles (locking, validation, migrations)
- **Developer expectations:** YAML configuration is familiar pattern for HA developers
- **Dual setup support:** Enables both YAML (dev/automation) and UI (end users) configuration paths

### Why Add YAML Support to the Integration?
The integration originally only supported UI-based config flow. Adding YAML support provides:
- **Reproducible dev environments:** Same config every time, committed to repository
- **Zero-click setup:** Developers don't manually configure via UI after each reset
- **CI/CD friendly:** Automated testing can use YAML without UI interaction
- **Documentation as code:** Config in `.devcontainer/configuration.yaml` serves as working example
- **Industry standard:** Most mature HA integrations support both YAML and UI configuration

### Why Auto-Generate Sample Media?
Sample test images are generated automatically during initialization rather than committed to repository:
- **Saves repository size:** Generated images would bloat git history unnecessarily
- **Consistent with tests:** Uses same `image_generator.py` that test suite uses
- **Fresh state guarantee:** Each init creates clean, known-good test data
- **Flexible testing:** Easy to modify test image specs without git churn
- **Single source of truth:** `TEST_IMAGE_SPECS` defines all test images in one place

The generator creates images with embedded XMP/EXIF metadata (ratings, tags) distributed across subdirectories (`by_year/dir_0`, `by_year/dir_1`) matching the structure test fixtures expect. This ensures both manual testing and automated tests use identical data.

### Why Configure Media Source?
Home Assistant's `media_source` integration was enabled to expose the sample media directory:
- **Real integration testing:** Allows testing media browsing functionality developers might add
- **UI visibility:** Sample images appear in HA's media browser for manual inspection
- **Path accessibility:** Ensures HA can access mounted directories (validation of permissions)
- **Complete environment:** Simulates production-like setup where media dirs must be accessible

The `media_dirs` configuration maps sample-media to a named source, making it browseable through Home Assistant's standard media UI.
