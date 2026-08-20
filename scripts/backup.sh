#!/usr/bin/env bash
# Kunlik zaxira nusxa. Cron ga qo'shing:
#   0 3 * * * /opt/luqma-ai/scripts/backup.sh >> /var/log/luqma-backup.log 2>&1
#
# SQLite faylni oddiy cp bilan nusxalash XAVFLI — yozuv o'rtasida ushlansa
# buzilgan nusxa chiqadi. Shuning uchun sqlite3 ning .backup buyrug'i
# ishlatiladi: u yozuvlar bilan to'g'ri kelishadi.

set -euo pipefail

LOYIHA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB="${LUQMA_DB:-$LOYIHA_DIR/data/luqma.db}"
ZAXIRA_DIR="${LUQMA_BACKUP_DIR:-$LOYIHA_DIR/backups}"
SAQLASH_KUNI="${LUQMA_BACKUP_DAYS:-14}"

mkdir -p "$ZAXIRA_DIR"

if [[ ! -f "$DB" ]]; then
  echo "[$(date -Is)] XATO: DB topilmadi: $DB" >&2
  exit 1
fi

NOM="luqma-$(date +%Y%m%d-%H%M%S).db"
YOL="$ZAXIRA_DIR/$NOM"

sqlite3 "$DB" ".backup '$YOL'"
gzip -f "$YOL"

# Eski nusxalarni tozalaymiz.
find "$ZAXIRA_DIR" -name 'luqma-*.db.gz' -mtime "+$SAQLASH_KUNI" -delete

echo "[$(date -Is)] Zaxira tayyor: $NOM.gz ($(du -h "$YOL.gz" | cut -f1))"
