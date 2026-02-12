# nfo — TODO / Roadmap

## ✅ Done (v0.2.3)

### Core
- [x] `@log_call`, `@catch` decorators
- [x] `@logged` — class decorator (auto-wrap all public methods)
- [x] `@skip` — exclude methods from `@logged`
- [x] `auto_log()` — module-level patching (one call = all functions logged)
- [x] `auto_log_by_name()` — same but accepts module name strings
- [x] `Logger` — central dispatcher with multiple sinks
- [x] `configure()` — one-liner project setup with sink specs, env overrides
- [x] `configure(force=True)` — re-configuration guard
- [x] Async support: `@log_call`, `@catch`, `@logged` transparently handle `async def`
- [x] Duplicate log fix: `propagate=False` prevents double output
- [x] `_StdlibBridge` — forward stdlib `logging.getLogger()` to nfo sinks

### Sinks
- [x] `SQLiteSink`, `CSVSink`, `MarkdownSink`
- [x] `JSONSink` — structured JSON Lines output for ELK/Grafana Loki
- [x] `PrometheusSink` — export metrics (duration, error rate, call count) to Prometheus
- [x] `WebhookSink` — HTTP POST alerts to Slack/Discord/Teams on ERROR
- [x] `configure()` supports `json:path` and `prometheus:port` sink specs

### Environment & Analysis
- [x] `EnvTagger` — auto-tag logs with environment/trace_id/version
- [x] `DynamicRouter` — route logs by env/level/custom rules
- [x] `DiffTracker` — detect output changes between versions
- [x] `LLMSink` — LLM-powered log analysis via litellm
- [x] `detect_prompt_injection()` — regex prompt injection detection

### DevOps & Multi-language
- [x] Docker Compose demo: FastAPI app + Prometheus + Grafana (pre-built dashboard)
- [x] Grafana dashboard: calls/s, error rate, p95 duration, histogram, top functions
- [x] Load generator: `demo/load_generator.py`
- [x] Root `Dockerfile` + `examples/docker-compose-service.yml` (centralized logging service)
- [x] Kubernetes manifests: Deployment + Service + PVC
- [x] gRPC proto definition (`examples/nfo.proto`)
- [x] HTTP logging service (`examples/http_service.py`) — FastAPI, multi-language endpoint
- [x] Multi-language clients: Bash (`bash_client.sh`), Go (`go_client.go`), Rust (`rust_client.rs`)
- [x] `.env.example` files (root + examples/) with all `NFO_*` variables
- [x] `bump2version` config synced: `pyproject.toml`, `VERSION`, `nfo/__init__.py` bump atomically

### Quality
- [x] 114 tests passing (Python 3.13)
- [x] All Python examples verified and runnable
- [x] README with comparison table (polog, logdecorator, loguru, structlog)
- [x] CHANGELOG.md
- [x] Integration: pactown + pactown-com

## 🔜 Next (v0.3.x)

### New Sinks

- [ ] `OTELSink` — OpenTelemetry spans for distributed tracing (Jaeger/Zipkin via OTLP)
- [ ] `ElasticsearchSink` — direct Elasticsearch indexing for production log aggregation

### Web Dashboard

- [ ] Standalone `nfo-dashboard` CLI: `nfo dashboard --db logs.db`
- [ ] Filter by `trace_id`, `environment`, `level`, `function_name`, date range
- [ ] REST API: `GET /query?env=prod&level=ERROR&last=24h`

### Replay & Testing

- [ ] `replay_logs()` — replay function calls from SQLite logs for regression testing
- [ ] `replay_from_sqlite("logs.db", max_calls=100)` — bounded replay

### Core Improvements

- [ ] Log viewer CLI: `nfo query logs.db --level ERROR --last 24h`
- [ ] Log rotation for file-based sinks (CSV, Markdown, JSON)
- [ ] Sampling: log only N% of calls for high-throughput functions
- [ ] GitHub Actions integration: auto-comment LLM analysis on failed CI builds

### Composable Pipeline (achieved ✅)

```python
# Full monitoring stack (working in v0.2.0)
sink = PrometheusSink(       # metrics → Grafana
    WebhookSink(             # alerts → Slack
        EnvTagger(           # tagging
            SQLiteSink("logs.db")
        ),
        url="https://hooks.slack.com/...",
        levels=["ERROR"],
    ),
    port=9090,
)
```

## 💡 Ideas

- `GraphQLSink` — GraphQL query interface over SQLite logs
- `PineconeSink` / `VectorSink` — semantic log search via embeddings
- LangChain/LlamaIndex integration for semantic log search
- Auto-generate unit tests from logged function calls
- Anomaly detection: flag unusual arg patterns or duration spikes
- Cost tracking for LLM sink (tokens used per analysis)
- Plugin system for custom sinks (register via entry_points)
- RPi/embedded mode: minimal memory footprint, circular buffer sink