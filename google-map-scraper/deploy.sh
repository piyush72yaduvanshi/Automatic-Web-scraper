#!/usr/bin/env bash
# ==============================================================================
# Google Maps Scraper Engine — Autonomous Linux Server Installer & Starter
# Works on: Ubuntu 20.04+, Debian 11+, Debian 12+, CentOS 9+
# ==============================================================================

set -euo pipefail

echo "=========================================================="
echo "🚀 Google Maps Scraper Engine — Server Setup"
echo "=========================================================="

# 1. Check Python
if ! command -v python3 &>/dev/null; then
    echo "▶ Installing Python 3..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update && sudo apt-get install -y python3 python3-pip
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3 python3-pip
    fi
fi

# 2. Check / Install Chromium for headless scraping
if ! command -v chromium &>/dev/null && ! command -v google-chrome &>/dev/null; then
    echo "▶ Installing Chromium and graphic libraries for headless scraping..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update && sudo apt-get install -y chromium \
            libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
            libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
            libpango-1.0-0 libcairo2 libasound2 curl
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y chromium
    fi
    echo "✓ Chromium installed successfully."
else
    echo "✓ Detected existing Chrome/Chromium installation."
fi

# 3. Create .env if missing
if [ ! -f .env ]; then
    echo "▶ Creating default .env configuration..."
    cp .env.example .env
fi

# 4. Optional: Setup systemd service if requested
if [ "${1:-}" == "--service" ]; then
    echo "▶ Installing systemd background service..."
    INSTALL_DIR="$(pwd -P)"
    sed -i "s|/opt/google-map-scraper|${INSTALL_DIR}|g" scripts/google-maps-scraper.service
    sudo cp scripts/google-maps-scraper.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable google-maps-scraper
    sudo systemctl restart google-maps-scraper
    echo "✓ Service installed and started!"
    echo "  Check status: sudo systemctl status google-maps-scraper"
    exit 0
fi

# 5. Start engine directly
echo "=========================================================="
echo "▶ Starting Scraper Microservice on http://0.0.0.0:8080..."
echo "=========================================================="
export SCRAPER_ALLOW_REMOTE=1
python3 engine/serve.py --host 0.0.0.0 --port 8080 --allow-remote
