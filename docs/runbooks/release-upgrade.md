# Release and Upgrade Runbook

## Versioning

This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

- `MAJOR` — incompatible API or schema changes requiring consumer action.
- `MINOR` — new features, endpoints, or schema additions that are backward compatible.
- `PATCH` — bug fixes, security patches, documentation corrections, or data refreshes.

## Cutting a release

1. **Ensure `main` is green.**
   All CI checks must pass on the commit you intend to tag.

2. **Update `CHANGELOG.md`.**
   Move items from `## [Unreleased]` into a new versioned section:
   ```markdown
   ## [0.1.1] - 2026-07-10
   ### Added
   - ...
   ### Fixed
   - ...
   ```

3. **Bump the version in `pyproject.toml`.**
   ```toml
   version = "0.1.1"
   ```

4. **Commit the changelog and version bump.**
   ```bash
   git add CHANGELOG.md pyproject.toml
   git commit -m "chore: release v0.1.1"
   ```

5. **Create and push a signed tag.**
   ```bash
   git tag -s v0.1.1 -m "Release v0.1.1"
   git push origin main v0.1.1
   ```

6. **Verify the release workflow.**
   The `.github/workflows/release.yml` workflow builds and pushes:
   - `ghcr.io/bmsull560/fcc-router-consumer-awareness:v0.1.1`
   - `ghcr.io/bmsull560/fcc-router-consumer-awareness:latest`

7. **Publish release notes.**
   Use the GitHub release page or a `RELEASE_NOTES.md` file to summarize:
   - Highlights
   - Breaking changes (if any)
   - Migration steps
   - Links to the relevant runbooks

## Upgrading a deployment

1. **Back up the existing database.**
   ```bash
   docker compose down
   python scripts/backup_db.py
   ```

2. **Pull the new image and run migrations.**
   Follow the [Deployment Runbook](./deployment.md).

3. **Verify health and metrics.**
   ```bash
   curl -f http://localhost:8000/healthz
   curl -f http://localhost:8000/ready
   curl -f http://localhost:8000/metrics
   ```

4. **Monitor SLOs.**
   Watch error rate and p99 latency for 15 minutes. If thresholds are breached, follow the [Rollback Runbook](./rollback.md).

## Rolling back

See the [Rollback Runbook](./rollback.md).
