---
name: homeassistant-playwright-integration-test
description: Test Home Assistant custom integrations using Playwright browser automation. Use when you need to verify integration functionality in a running Home Assistant instance, test UI components, dashboards, or config flows. Covers launching HA via VSCode tasks, logging in, navigating dashboards, and verifying entities.
compatibility: Requires Firefox browser dependencies (libxcomposite1, libxdamage1, libgtk-3-0, libatk1.0-0), Playwright MCP server, and VSCode tasks configured for Home Assistant
metadata:
  author: rabefabi
  version: "1.0"
---

# Home Assistant Playwright Integration Test

This skill covers end-to-end testing of Home Assistant custom integrations using Playwright browser automation.

## Prerequisites

Before running this skill, ensure:

1. Home Assistant is configured in `.haconfig/` directory
2. Integration is configured in `configuration.yaml`
3. VSCode tasks are set up for Home Assistant lifecycle
4. Playwright MCP server is available with Firefox installed
5. Browser dependencies are installed in the container

## Step-by-Step Testing Process

### 1. Stop Any Running Home Assistant Instances

First, ensure no Home Assistant processes are running:

```bash
pkill -f "hass.*haconfig" || true
```

### 2. Launch Home Assistant via VSCode Task

Use the VSCode command to run the task:

```javascript
// Use run_vscode_command tool
workbench.action.tasks.runTask with argument: "Initialize Home Assistant (Headless)"
```

This task will:
- Reset the Home Assistant configuration
- Copy configuration files from `.devcontainer/`
- Start Home Assistant in the background
- Create the admin user automatically
- Mark onboarding as complete

### 3. Install Playwright Browser (First Time Only)

If Firefox is not installed, install it:

```javascript
mcp_playwright_browser_install with browser: "firefox"
```

### 4. Navigate to Home Assistant

```javascript
mcp_playwright_browser_navigate to url: "http://localhost:8123"
```

Expected: You'll be redirected to the login page.

### 5. Log In

**Login Screen:**
- Fill username field (ref: textbox "Username"): `admin`
- Fill password field (ref: textbox "Password"): `dev-password`
- Click "Log in" button

Expected: You'll be logged in and taken directly to the overview page (onboarding is already complete).

### 6. Navigate to Integration Dashboard

After logging in, navigate to the integration's dashboard:

```javascript
mcp_playwright_browser_navigate to url: "http://localhost:8123/lovelace-slideshow/0"
```

Replace `lovelace-slideshow` with your dashboard path configured in `configuration.yaml`.

### 7. Verify Integration Components

Use `mcp_playwright_browser_snapshot` to inspect the page structure and verify:

**Required Elements:**
- Sidebar contains dashboard link (e.g., "Slideshow Demo")
- Image entity card displays with metadata overlay and timestamp
- Image displays generated test image (solid color background with metadata text on top)
- Statistics card shows four sensor values:
  - "Matching Images" - should match expected count (e.g., 16)
  - "Total Discovered" - total files scanned
  - "Failed Images" - count of unreadable files
  - "Non-Image Files" - count of non-image files found
- Description text renders correctly below statistics

**Image Advancement Verification:**
- Note the timestamp on the image (e.g., "February 13, 2026 at 4:06 PM")
- Wait 10-15 seconds and take another screenshot
- Verify timestamp has updated and image color has changed
- This confirms the slideshow is advancing automatically

**Log Verification:**
- Check integration logs: `tail -20 .haconfig/homeassistant.log | grep -i "metadata_slideshow"`
- Should see repeated "Finished fetching" messages every 10 seconds
- All fetches should show `(success: True)` with minimal execution time (&lt;0.01s typically)

### 8. Take Screenshots for Documentation

Capture the current state:

```javascript
mcp_playwright_browser_take_screenshot with type: "jpeg"
```

This saves to `.playwright-mcp/page-TIMESTAMP.jpeg` for review.

### 9. Clean Up

Close the browser when done:

```javascript
mcp_playwright_browser_close
```

To stop Home Assistant, interrupt the task or kill the process.

## Common Issues and Solutions

### Issue: Browser dependencies missing

**Symptom:** Error about missing libraries (libXcomposite.so.1, libgtk-3.so.0, etc.)

**Solution:** Install dependencies:
```bash
sudo apt-get update && sudo apt-get install -y libxcomposite1 libxdamage1 libgtk-3-0 libatk1.0-0
```

Add these to `Dockerfile` for future development.

### Issue: Home Assistant stuck in recovery mode

**Symptom:** HA starts but shows recovery mode in logs

**Solution:** Validate configuration:
```bash
uv run hass --config .haconfig --script check_config
```

Fix any configuration errors reported.

### Issue: Integration not loading

**Symptom:** Integration doesn't appear in onboarding or dashboard

**Solution:** 
1. Check logs: `grep -i "your_integration" .haconfig/home-assistant.log`
2. Verify integration is in `custom_components/` directory
3. Ensure `PYTHONPATH` includes integration directory
4. Check `manifest.json` dependencies are installed

### Issue: Can't find elements in Playwright

**Symptom:** Element refs don't match or click fails

**Solution:** 
1. Use `mcp_playwright_browser_snapshot` to see current structure
2. Look for elements by role and name, not by ref numbers (refs can change)
3. Wait for dynamic content to load before interacting

## Integration-Specific Notes

### metadata-slideshow-helper

- **Dashboard path:** `/lovelace-slideshow/0`
- **Expected entities:**
  - Image: `image.metadata_slideshow_helper`
  - Sensors: `sensor.matching_image_count`, `sensor.discovered_image_count`, `sensor.failed_image_count`, `sensor.non_image_file_count`
- **Test images location:** `sample-media/` directory
- **Configuration:** See `.devcontainer/configuration.yaml`

### Custom Integration Template

For other integrations, update:
1. Dashboard path in navigation step
2. Entity names to verify
3. Expected sensor values
4. Integration-specific configuration

## Best Practices

1. **Always validate configuration** before starting HA to catch errors early
2. **Use descriptive element selectors** (role + name) instead of refs for stability
3. **Take screenshots** at key verification points for debugging
4. **Check logs** if integration doesn't behave as expected
5. **Clean state** between test runs by resetting HA configuration

## Reference Files

- Configuration template: `.devcontainer/configuration.yaml`
- Lovelace dashboard: `.devcontainer/lovelace-slideshow.yaml`
- Init script: `scripts/init-headless`
- Start script: `scripts/start`
- VSCode tasks: `.vscode/tasks.json`
