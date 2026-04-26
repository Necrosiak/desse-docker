#!/usr/bin/env bash
# =============================================================================
# NetworkMemories — Demon's Souls — Backup Script
# Backs up the db/ directory (messages, ghosts, bloodstains pickle files)
# =============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"
echo "📦 Starting DeSSE backup..."

tar czf "$BACKUP_DIR/desse_$DATE.tar.gz" -C "$ROOT_DIR" db/
echo "✅ Backup: $BACKUP_DIR/desse_$DATE.tar.gz"

# Keep last 7
ls -t "$BACKUP_DIR"/*.tar.gz 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null || true
echo "🧹 Old backups pruned (keeping last 7)"
