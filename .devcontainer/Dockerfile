FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# System dependencies for audio processing and NTP-related tooling
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        ffmpeg \
        curl \
        jq \
        ca-certificates \
        build-essential \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Install backend dependencies (editable install into the dev container)
COPY backend/pyproject.toml /tmp/backend-pyproject.toml
RUN pip install --upgrade pip

# Keep the source mounted; installs happen in post-create.
