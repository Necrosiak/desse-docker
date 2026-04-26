#!/usr/bin/env bash
# =============================================================================
# NetworkMemories — Demon's Souls — Restore Script
# =============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"

if [ -n "${1:-}" ]; then
  BACKUP_FILE="$1"
else
  LATEST=$(ls -t "$BACKUP_DIR"/*.tar.gz 2>/dev/null | head -n1)
  [ -z "$LATEST" ] && { echo "❌ No backup found in $BACKUP_DIR"; exit 1; }
  BACKUP_FILE="$LATEST"
fi

echo "⚠️  Will restore: $(basename "$BACKUP_FILE")"
read -rp "Type 'yes' to confirm: " CONFIRM
[ "$CONFIRM" = "yes" ] || { echo "Aborted."; exit 0; }

tar xzf "$BACKUP_FILE" -C "$ROOT_DIR"
echo "✅ Restore complete. Restart with: make run-daemon"
