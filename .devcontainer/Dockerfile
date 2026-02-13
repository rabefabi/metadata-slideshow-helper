FROM mcr.microsoft.com/devcontainers/python:3.13-bookworm

# Install Node.js, npm for MCP servers, and ffmpeg for media processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install uv for dependency management
# NOTE: Ensure that version number is in sync with .github/workflows/pre-commit.yaml
ARG UV_VERSION=0.10.2
ENV UV_INSTALL_DIR=/usr/local/bin
RUN curl -LsSf https://astral.sh/uv/${UV_VERSION}/install.sh | sh
# Use copy link mode for compatibility with devcontainer mounts on different filesystems
ENV UV_LINK_MODE=copy
