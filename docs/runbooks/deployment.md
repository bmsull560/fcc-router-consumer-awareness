# Deployment Runbook

## Prerequisites

- Docker and Docker Compose installed on the target host.
- Access to the GitHub Container Registry image `ghcr.io/bmsull560/fcc-router-consumer-awareness`.
- A backup of the existing database (`python scripts/backup_db.py`).
- If the database is not at the default path, set `FCC_DB_PATH` (e.g., `export FCC_DB_PATH=/path/to/fcc_router_consumer_awareness.db`).

## Steps

> **Bind-mount ownership:** The container image runs as the non-root `appuser`
> user. Host directories `./data` and `./backups` must be writable by that UID,
> or you must override the user in `docker-compose.yml` with
> `user: "${UID}:${GID}"` after aligning directory ownership.

1. **Pull the desired image version.**
   ```bash
   docker pull ghcr.io/bmsull560/fcc-router-consumer-awareness:vX.Y.Z
   ```

2. **Stop the running container.**
   ```bash
   docker compose down
   ```

3. **Run migrations.**
   ```bash
   docker run --rm -v ./data:/app/data ghcr.io/bmsull560/fcc-router-consumer-awareness:vX.Y.Z \
     python scripts/migrate.py migrate
   ```

4. **Start the new version.**
   ```bash
   docker compose up -d
   ```

5. **Verify health.**
   ```bash
   curl -f http://localhost:8000/healthz
   curl -f http://localhost:8000/ready
   curl -f http://localhost:8000/metrics
   ```

## Rollback

If the deployment fails verification, follow the [Rollback Runbook](./rollback.md).
