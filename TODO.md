# nfo — TODO / Roadmap

## ✅ Done

- [x] Core: `@log_call`, `@catch` decorators
- [x] Sinks: `SQLiteSink`, `CSVSink`, `MarkdownSink`
- [x] `Logger` — central dispatcher with multiple sinks
- [x] `configure()` — one-liner project setup with sink specs, env overrides
- [x] `@logged` — class decorator (auto-wrap all public methods)
- [x] `@skip` — exclude methods from `@logged`
- [x] `auto_log()` — module-level patching (one call = all functions logged)
- [x] `_StdlibBridge` — forward stdlib `logging.getLogger()` to nfo sinks
- [x] `LLMSink` — LLM-powered log analysis via litellm
- [x] `detect_prompt_injection()` — regex prompt injection detection
- [x] `EnvTagger` — auto-tag logs with environment/trace_id/version
- [x] `DynamicRouter` — route logs by env/level/custom rules
- [x] `DiffTracker` — detect output changes between versions
- [x] Integration: pactown (`nfo_config.py` + cli.py + runner_api.py)
- [x] Integration: pactown-com (`nfo_config.py` + main.py)
- [x] 73 tests passing
- [x] README with comparison table, integration guide, LLM features
- [x] CHANGELOG.md

## 🔜 Next

- [ ] Async support: `@async_log_call` for async/await functions
- [ ] `ElasticsearchSink` — for production log aggregation
- [ ] `PineconeSink` / `VectorSink` — semantic log search via embeddings
- [ ] GitHub Actions integration: auto-comment LLM analysis on failed CI builds
- [ ] Log viewer CLI: `nfo query logs.db --level ERROR --last 24h`
- [ ] Log rotation for file-based sinks (CSV, Markdown)
- [ ] Sampling: log only N% of calls for high-throughput functions
- [ ] Structured JSON sink for ELK/Grafana Loki
- [ ] OpenTelemetry span integration (attach nfo entries to OTEL traces)
- [ ] Dashboard: web UI for browsing SQLite logs

## 💡 Ideas

- LangChain/LlamaIndex integration for semantic log search
- Auto-generate unit tests from logged function calls
- Anomaly detection: flag unusual arg patterns or duration spikes
- Cost tracking for LLM sink (tokens used per analysis)
- Plugin system for custom sinks (register via entry_points)
- RPi/embedded mode: minimal memory footprint, circular buffer sink