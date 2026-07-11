#!/bin/bash

# ─────────────────────────────────────────────
# Raco AI Assessment - Clean Rebuild Script
# ─────────────────────────────────────────────

set -e  # Exit immediately if any command fails

echo "🧹 Stopping and removing existing containers..."
sudo docker compose down

echo ""
echo "🔨 Rebuilding images with no cache..."
sudo docker compose build --no-cache

echo ""
echo "🚀 Starting all containers..."
sudo docker compose up -d

echo ""
echo "✅ Clean rebuild complete!"
echo "📡 Django API is running at: http://localhost:8000"
echo ""
echo "📋 Useful commands:"
echo "  View logs:        docker compose logs -f"
echo "  Stop containers:  ./stop.sh"
