# Incident Response Runbook

## Detection

- Monitor `/healthz` and `/ready` endpoints.
- Watch Prometheus metrics at `/metrics` for 5xx rates or latency spikes.
- Alert on failed container health checks.

## Triage

1. Check service health.
   ```bash
   curl http://localhost:8000/healthz
   curl http://localhost:8000/ready
   ```

2. Check recent logs.
   ```bash
   docker compose logs --tail 100 api
   ```

3. Check database integrity.
   ```bash
   python scripts/validate_db.py
   sqlite3 data/fcc_router_consumer_awareness.db "PRAGMA integrity_check;"
   ```

## Common Issues

- **Database locked:** Verify only one process is writing to the SQLite file.
- **500 errors:** Look for `unhandled_exception` logs and note the `trace_id`.
- **Rate limiting:** Check if legitimate traffic is being throttled on `/api/search`.

## Escalation

If the issue cannot be resolved quickly, follow the [Rollback Runbook](./rollback.md) or [Disaster Recovery Runbook](./disaster-recovery.md).

## Monitoring and SLOs

See [SLOs and Alert Examples](./slos-alerts.md) for defined objectives, SLIs, and copy-pasteable Prometheus alerting rules.
