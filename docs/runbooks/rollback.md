# Rollback Runbook

## Automated rollback via GitHub Actions

1. Go to **Actions > Rollback** in the repository.
2. Click **Run workflow**.
3. Enter the version tag to roll back to (e.g., `v0.1.0`).
4. Click **Run workflow**.
5. The workflow retags the selected image as `latest` in GHCR.

## Manual rollback

1. Pull the previous image version.
   ```bash
   docker pull ghcr.io/bmsull560/fcc-router-consumer-awareness:vX.Y.Z
   docker tag ghcr.io/bmsull560/fcc-router-consumer-awareness:vX.Y.Z \
     ghcr.io/bmsull560/fcc-router-consumer-awareness:latest
   docker push ghcr.io/bmsull560/fcc-router-consumer-awareness:latest
   ```

2. Redeploy:
   ```bash
   docker compose down
   docker compose up -d
   ```

3. Verify health.
   ```bash
   curl -f http://localhost:8000/healthz
   curl -f http://localhost:8000/ready
   ```
