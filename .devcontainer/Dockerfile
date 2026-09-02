FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# The base Microsoft dev image ships a yarn apt source whose signing key is
# missing, which makes `apt-get update` fail ("repository is not signed").
# Remove it before updating. ffmpeg (audio) and jq are the only extras needed;
# curl, ca-certificates, git and build-essential are already in the base image.
RUN rm -f /etc/apt/sources.list.d/yarn.list /etc/apt/sources.list.d/yarn*.list \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get update -o Acquire::Retries=3 \
    && apt-get -y install --no-install-recommends \
        ffmpeg \
        jq \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Install backend dependencies (editable install into the dev container)
COPY backend/pyproject.toml /tmp/backend-pyproject.toml
RUN pip install --upgrade pip

# Keep the source mounted; installs happen in post-create.
