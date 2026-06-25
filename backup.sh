#!/usr/bin/env bash
set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BACKUP_DIR="$HOME/budget-backups"
mkdir -p "$BACKUP_DIR"

POSTGRES_USER=$(grep -E '^POSTGRES_USER=' "$SCRIPT_DIR/.env" | cut -d= -f2 | tr -d '[:space:]"')
POSTGRES_DB=$(grep -E '^POSTGRES_DB=' "$SCRIPT_DIR/.env" | cut -d= -f2 | tr -d '[:space:]"')

FILENAME="$BACKUP_DIR/budget_$(date +%Y%m%d_%H%M%S).sql"
cd "$SCRIPT_DIR"
docker compose exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$FILENAME"

# Keep only the last 30 days of backups
find "$BACKUP_DIR" -name "budget_*.sql" -mtime +30 -delete

echo "Backup saved: $FILENAME"
