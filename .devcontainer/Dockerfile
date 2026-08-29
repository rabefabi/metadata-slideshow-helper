FROM mcr.microsoft.com/devcontainers/python:3.13-bookworm

# Install Node.js 20+ (required for Playwright MCP), npm, ffmpeg, and browser dependencies
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    ffmpeg \
    libxcomposite1 \
    libxdamage1 \
    libgtk-3-0 \
    libatk1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install uv for dependency management
# NOTE: Ensure that version number is in sync with .github/workflows/pre-commit.yaml
ARG UV_VERSION=0.10.2
ENV UV_INSTALL_DIR=/usr/local/bin
RUN curl -LsSf https://astral.sh/uv/${UV_VERSION}/install.sh | sh
# Use copy link mode for compatibility with devcontainer mounts on different filesystems
ENV UV_LINK_MODE=copy
