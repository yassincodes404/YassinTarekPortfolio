#!/bin/bash
# Backup script for portfolio DB and uploads
# Usage: ./scripts/backup.sh [destination_dir]

set -e

DEST=${1:-./backups}
DATE=$(date +%Y-%m-%d_%H%M%S)
DATA_DIR=${DATA_DIR:-/data}

mkdir -p "$DEST"

echo "Backing up database..."
cp "$DATA_DIR/data.db" "$DEST/data-$DATE.db"

echo "Backing up uploads..."
tar -czf "$DEST/uploads-$DATE.tar.gz" -C "$DATA_DIR" uploads/

echo "Backup complete:"
ls -lh "$DEST"/*$DATE*

# Cleanup: keep only last 30 days
find "$DEST" -name "data-*.db" -mtime +30 -delete 2>/dev/null || true
find "$DEST" -name "uploads-*.tar.gz" -mtime +30 -delete 2>/dev/null || true
