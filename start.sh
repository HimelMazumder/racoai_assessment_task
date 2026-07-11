#!/bin/bash

# ─────────────────────────────────────────────
# Raco AI Assessment - Project Startup Script
# ─────────────────────────────────────────────

set -e  # Exit immediately if any command fails

echo "🚀 Starting Raco AI Backend..."

# Build images and start all containers in the background
sudo docker compose up --build -d

echo ""
echo "✅ All containers are up!"
echo "📡 Django API is running at: http://localhost:8000"
echo ""
echo "📋 Useful commands:"
echo "  View logs:        docker compose logs -f"
echo "  Stop containers:  docker compose down"
echo "  Stop + wipe DB:   docker compose down -v"
