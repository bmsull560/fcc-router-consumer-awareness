# SLOs and Alert Examples

## Service-Level Objectives

| SLO | Target | SLI | Measurement |
|-----|--------|-----|-------------|
| Availability | 99.9% over 30 days | `/healthz` and `/ready` success rate | Prometheus `up` and `http_request_duration_seconds_count{status=~"2..|3.."}` |
| Latency p99 | < 500 ms | Response time for `/api/*` | Prometheus histogram `http_request_duration_seconds_bucket{le="0.5"}` |
| Error rate | < 0.1% | 5xx responses across all routes | Prometheus `rate(http_request_duration_seconds_count{status=~"5.."}[5m])` |
| Rate-limit fairness | < 1% of legitimate requests throttled | 429 responses on `/api/search` | Prometheus `rate(http_request_duration_seconds_count{status="429"}[5m])` |

## Prometheus alerting rules

Save these as `prometheus-rules.yml` in your monitoring repository:

```yaml
groups:
  - name: fcc-router-consumer-awareness
    rules:
      - alert: FCCRouterAPIDown
        expr: up{job="fcc-router-consumer-awareness"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "FCC Router Consumer Awareness API is down"

      - alert: FCCRouterAPIHighErrorRate
        expr: |
          sum(rate(http_request_duration_seconds_count{status=~"5.."}[5m]))
          /
          sum(rate(http_request_duration_seconds_count[5m])) > 0.001
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High 5xx error rate on FCC Router API"

      - alert: FCCRouterAPIHighLatency
        expr: |
          histogram_quantile(0.99,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
          ) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "FCC Router API p99 latency exceeds 500 ms"

      - alert: FCCRouterAPIDatabaseNotReady
        expr: ready_status{job="fcc-router-consumer-awareness"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "FCC Router API database readiness check is failing"
```

## Runbook links

- Incident response: [./incident-response.md](./incident-response.md)
- Rollback: [./rollback.md](./rollback.md)
- Disaster recovery: [./disaster-recovery.md](./disaster-recovery.md)
