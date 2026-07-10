# Disaster Recovery Runbook

## Restore from backup

1. List available backups.
   ```bash
   ls -la backups/
   ```

2. Stop the API.
   ```bash
   docker compose down
   ```

3. Restore the database. If the database is not at the default path, set `FCC_DB_PATH` first.
   ```bash
   export FCC_DB_PATH=data/fcc_router_consumer_awareness.db
   python scripts/restore_db.py backups/fcc_router_consumer_awareness_YYYYMMDD_HHMMSS.db.gz --force
   ```

4. Validate the restored database.
   ```bash
   python scripts/validate_db.py
   sqlite3 data/fcc_router_consumer_awareness.db "PRAGMA integrity_check;"
   ```

5. Restart the service.
   ```bash
   docker compose up -d
   ```

## If no backup is available

1. Recreate the database from the SQL dump.
   ```bash
   sqlite3 data/fcc_router_consumer_awareness.db < data/fcc_router_consumer_awareness.sql
   ```
2. Re-run migrations to bring it up to date.
   ```bash
   python scripts/migrate.py migrate
   ```
3. Validate and restart.
