# ============================================
# While Health - Script de Backup Automatique
# ============================================

#!/bin/bash

# Configuration
BACKUP_DIR="/var/backups/while_health"
RETENTION_DAYS=30
DB_NAME="while_health"
DB_USER="while_health_user"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Créer le répertoire de backup s'il n'existe pas
mkdir -p $BACKUP_DIR

echo "🚀 Starting backup process at $(date)"

# Backup de la base de données
echo "📊 Backing up PostgreSQL database..."
pg_dump -U $DB_USER -h localhost $DB_NAME > $BACKUP_DIR/db_backup_$TIMESTAMP.sql

if [ $? -eq 0 ]; then
    echo "✅ Database backup completed"
else
    echo "❌ Database backup failed"
    exit 1
fi

# Backup des fichiers médias
echo "📁 Backing up media files..."
tar -czf $BACKUP_DIR/media_backup_$TIMESTAMP.tar.gz /path/to/media/

if [ $? -eq 0 ]; then
    echo "✅ Media backup completed"
else
    echo "❌ Media backup failed"
    exit 1
fi

# Compression du backup DB
echo "🗜️ Compressing database backup..."
gzip $BACKUP_DIR/db_backup_$TIMESTAMP.sql

# Calcul de la taille des backups
DB_SIZE=$(du -h $BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz | cut -f1)
MEDIA_SIZE=$(du -h $BACKUP_DIR/media_backup_$TIMESTAMP.tar.gz | cut -f1)

echo "📏 Backup sizes: DB=$DB_SIZE, Media=$MEDIA_SIZE"

# Nettoyage des anciens backups
echo "🧹 Cleaning old backups..."
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "media_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Vérification de l'intégrité
echo "🔍 Verifying backup integrity..."
if gunzip -c $BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz | head -n 10 > /dev/null; then
    echo "✅ Database backup integrity OK"
else
    echo "❌ Database backup corrupted"
    exit 1
fi

# Notification (optionnel - intégrer avec monitoring)
echo "📧 Sending notification..."
curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"Backup completed successfully - DB: '$DB_SIZE', Media: '$MEDIA_SIZE'"}' \
    $SLACK_WEBHOOK_URL

echo "🎉 Backup process completed successfully at $(date)"

# Script de restauration (pour référence)
cat > $BACKUP_DIR/restore.sh << 'EOF'
#!/bin/bash
# Script de restauration
# Usage: ./restore.sh db_backup_20231201_120000.sql.gz

BACKUP_FILE=$1
DB_NAME="while_health"
DB_USER="while_health_user"

echo "🔄 Starting restore process..."

# Restaurer la DB
gunzip -c $BACKUP_FILE | psql -U $DB_USER -h localhost $DB_NAME

if [ $? -eq 0 ]; then
    echo "✅ Database restore completed"
else
    echo "❌ Database restore failed"
    exit 1
fi

echo "🎉 Restore process completed"
EOF

chmod +x $BACKUP_DIR/restore.sh