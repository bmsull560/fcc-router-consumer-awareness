# Load-Testing Runbook

## Baseline target

Run on a host comparable to the production deployment (CPU/memory class).

| Metric | Target |
|--------|--------|
| RPS | >= 100 requests/second |
| p99 latency | < 500 ms |
| Error rate | < 0.1% |
| CPU utilization | < 80% at target RPS |

## Run locally

1. Start the API in production-like mode:
   ```bash
   make api
   ```

2. Run Locust:
   ```bash
   .venv/Scripts/locust -f locustfile.py --host http://localhost:8000 -u 50 -r 10 -t 60s --headless
   ```

3. Capture the output (RPS, p99, failures) and record it in this runbook or in a release note.

## Interpretation

- If p99 latency exceeds 500 ms, check the SQLite query plans and consider adding indexes or caching.
- If error rate is > 0.1%, check `unhandled_exception` logs by `trace_id`.
- If `/api/search` returns many 429s, tune the rate limit or add more workers.
