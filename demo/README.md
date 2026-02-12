# nfo DevOps Demo

Full monitoring stack demonstrating all nfo sinks with Prometheus + Grafana.

## Quick Start

```bash
docker compose up --build
```

## Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **nfo-demo** (FastAPI) | http://localhost:8000 | — |
| **Prometheus** | http://localhost:9091 | — |
| **Grafana** | http://localhost:3000 | admin / admin |

## Demo Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Health check |
| `GET /demo/success` | Run successful decorated function calls |
| `GET /demo/error` | Trigger ERROR-level logs (division by zero, invalid user) |
| `GET /demo/slow` | Slow function — demonstrates duration histograms |
| `GET /demo/batch` | Batch of 30+ mixed calls for load simulation |
| `GET /metrics` | Prometheus metrics in text format |
| `GET /logs?level=ERROR&limit=20` | Browse SQLite logs as JSON |

## Generate Load

Populate dashboards with realistic traffic:

```bash
# From repo root:
python demo/load_generator.py --url http://localhost:8000 --interval 0.5

# Or with limited requests:
python demo/load_generator.py --count 100 --interval 0.2
```

## Sink Pipeline

```
@log_call / @catch / @logged
        │
        ▼
    EnvTagger (environment, trace_id, version)
        │
        ├──▶ PrometheusSink ──▶ Prometheus ──▶ Grafana dashboard
        │        └──▶ SQLiteSink ──▶ /logs endpoint
        │
        ├──▶ JSONSink ──▶ logs.jsonl (ELK / Loki ready)
        │
        └──▶ WebhookSink ──▶ Slack / Discord (ERROR only)
```

## Grafana Dashboard

Pre-provisioned dashboard "nfo — Function Logging Overview" includes:

- **Total Calls** / **Total Errors** / **Error Rate %** / **Avg Duration**
- **Calls per second** by function (time series)
- **Errors per second** by function (time series)
- **Duration distribution** (histogram heatmap)
- **p95 duration** by function
- **Calls by level** (pie chart)
- **Top functions** by call count and error count (bar gauge)

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NFO_ENV` | `demo` | Environment tag for log entries |
| `NFO_VERSION` | `0.2.0` | Version tag |
| `NFO_LOG_DIR` | `/tmp/nfo-demo-logs` | Log file directory |
| `NFO_PROMETHEUS_PORT` | `9090` | Prometheus client HTTP port |
| `NFO_WEBHOOK_URL` | _(empty)_ | Slack/Discord webhook URL for ERROR alerts |

## Stop & Clean

```bash
docker compose down -v
```
