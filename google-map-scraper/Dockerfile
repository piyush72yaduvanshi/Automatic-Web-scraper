# Google Maps Scraper Engine — Dockerfile
# Python standard library only for the core scraper. Debian Chromium for headless scraping.

FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    chromium \
    curl \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --create-home --uid 10001 gmskit

WORKDIR /kit
COPY engine/ engine/
COPY scripts/ scripts/

RUN mkdir -p .engine/data && chown -R gmskit:gmskit .engine /kit

USER gmskit
ENV CHROME=/usr/bin/chromium \
    PYTHONUNBUFFERED=1 \
    SCRAPER_ALLOW_REMOTE=1

EXPOSE 8080

CMD ["python", "engine/serve.py", "--host", "0.0.0.0", "--port", "8080", "--allow-remote"]
