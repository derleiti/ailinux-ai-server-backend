#!/bin/bash
# WordPress Database Backup Script

set -e

BACKUP_DIR="/backup"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/wordpress_${TIMESTAMP}.sql.gz"

echo "[$(date)] Starting WordPress database backup..."

# Wait for database to be ready
while ! mariadb-admin ping -h "${WORDPRESS_DB_HOST}" -u root -p"${MYSQL_ROOT_PASSWORD}" --silent 2>/dev/null; do
    echo "[$(date)] Waiting for database..."
    sleep 5
done

# Create backup
mariadb-dump -h "${WORDPRESS_DB_HOST}" \
    -u root \
    -p"${MYSQL_ROOT_PASSWORD}" \
    --single-transaction \
    --routines \
    --triggers \
    "${WORDPRESS_DB_NAME}" | gzip > "${BACKUP_FILE}"

# Generate checksum
sha256sum "${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"

echo "[$(date)] Backup created: ${BACKUP_FILE}"

# Cleanup old backups
find "${BACKUP_DIR}" -name "wordpress_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
find "${BACKUP_DIR}" -name "wordpress_*.sql.gz.sha256" -mtime +${RETENTION_DAYS} -delete

echo "[$(date)] Cleanup complete. Keeping backups from last ${RETENTION_DAYS} days."

# Sleep until next backup (24 hours)
sleep 86400
