# reimap container image.
#
# Note: on Linux, scanning connections inside a container only sees the
# container's own network namespace. To observe the host's connections, run with
# --network host --pid host (and typically as root). This image is primarily for
# a quick, isolated look at the reimap UI.
FROM python:3.12-slim

LABEL org.opencontainers.image.title="reimap"
LABEL org.opencontainers.image.description="Local-first, real-time network map with an extensibility hook system."
LABEL org.opencontainers.image.authors="Batuhan Ayrıbaş <hello@batuhanayribas.com>"
LABEL org.opencontainers.image.url="https://batuhanayribas.com"
LABEL org.opencontainers.image.vendor="Rootcastle (https://rootcastle.com)"
LABEL org.opencontainers.image.licenses="MIT"

# lsof provides the macOS-style fallback scanner and is handy for debugging.
RUN apt-get update \
    && apt-get install -y --no-install-recommends lsof \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir .

EXPOSE 8050

# Bind to all interfaces inside the container and do not try to open a browser.
ENTRYPOINT ["reimap", "--host", "0.0.0.0", "--no-browser"]
