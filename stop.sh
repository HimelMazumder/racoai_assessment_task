#!/bin/bash

# ─────────────────────────────────────────────
# Raco AI Assessment - Project Stop Script
# ─────────────────────────────────────────────

echo "🛑 Stopping Raco AI Backend..."

# Stop and remove containers (preserves DB volume data)
sudo docker compose down

echo ""
echo "✅ All containers stopped."
echo ""
echo "💡 To also wipe the database volume, run:"
echo "   sudo docker compose down -v"
