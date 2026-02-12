# Changelog

All notable changes to `nfo` are documented here.

## [0.2.3] - 2026-02-12

### Fixed

- **`bump2version` config** — synced `.bumpversion.cfg` to track `pyproject.toml`, `VERSION`, and `nfo/__init__.py`; all three files now bump atomically
- **`env_tagger_usage.py`** — fixed `sqlite3.Row.get()` → `dict(row).get()` (Python 3.13 compat)
- **Stale pip install** — resolved nfo 0.1.17 in `site-packages` shadowing local source

### Added

- **Root `Dockerfile`** — used by `examples/docker-compose-service.yml` for centralized logging service
- **Multi-language examples** — verified and tested: Go client, Rust client, Bash client, gRPC proto, Kubernetes manifests, Docker Compose service stack
- **`.env.example` files** — root + `examples/` with all `NFO_*` variables documented

## [0.2.0] - 2026-02-12

### Added

- **`PrometheusSink`** — export function call metrics (duration histogram, call count, error rate) to Prometheus; auto `/metrics` endpoint; optional dep `pip install nfo[prometheus]`
- **`WebhookSink`** — HTTP POST alerts to Slack, Discord, or Microsoft Teams on ERROR; fire-and-forget with format templates; zero external dependencies (stdlib `urllib`)
- **`JSONSink`** — structured JSON Lines output for ELK/Grafana Loki/Fluentd; zero external dependencies
- **Docker Compose demo stack** — `nfo-demo` (FastAPI) + Prometheus + Grafana with pre-built dashboard
- **Grafana dashboard** — auto-provisioned: calls/s, error rate, p95 duration, histogram, top functions
- **Load generator** — `demo/load_generator.py` for populating metrics
- `configure()` now supports `json:path` and `prometheus:port` sink specs
- 27 new tests for `PrometheusSink`, `WebhookSink`, `JSONSink` (114 total)
- Optional dependency groups: `[prometheus]`, `[dashboard]`

### Changed

- Version bump to 0.2.0 (minor: new sinks, Docker Compose, DevOps integration)
- `pyproject.toml`: added `[prometheus]` and `[dashboard]` optional dependency groups
- `[dev]` group now includes `pytest-asyncio` and `prometheus_client`

## [0.1.19] - 2026-02-12

### Fixed

- **Duplicate log lines** — set `propagate=False` on stdlib logger to prevent double output
- **Re-configuration guard** — `configure()` now returns cached logger on repeated calls (use `force=True` to override)

## [0.1.18] - 2026-02-12

### Fixed

- Version sync between `__init__.py` and `pyproject.toml`

## [0.1.17] - 2026-02-12

### Fixed

- `__version__` in `__init__.py` synced with `pyproject.toml` (was out of date)

## [0.1.15] - 2026-02-12

### Added

- **Async support** — `@log_call`, `@catch`, and `@logged` now transparently handle `async def` functions via `inspect.iscoroutinefunction()`
- Async tests: 7 new tests for async `@log_call` and `@catch`

## [0.1.14] - 2026-02-11

### Added

- **`auto_log_by_name()`** — like `auto_log()` but accepts module name strings; resolves from `sys.modules`
- **`auto_log()`** — one-call module-level patching: wraps all functions in a module with `@log_call` or `@catch` without individual decorators
- `LogEntry` sinks now persist `environment`, `trace_id`, `version`, `llm_analysis` fields
- **Comparison table** with loguru, structlog, stdlib logging in README
- CHANGELOG.md, TODO.md

## [0.1.13] - 2026-02-11

### Added

- **`LLMSink`** — LLM-powered log analysis via litellm (OpenAI, Anthropic, Ollama)
- **`detect_prompt_injection()`** — regex-based prompt injection detection in function args
- **`EnvTagger`** — auto-tags logs with environment (prod/dev/ci/k8s/docker), trace_id, version
- **`DynamicRouter`** — routes logs to different sinks based on env/level/custom rules
- **`DiffTracker`** — detects output changes between function versions (A/B testing)
- `LogEntry` extended with `environment`, `trace_id`, `version`, `llm_analysis` fields
- `configure()` extended with `llm_model`, `environment`, `version`, `detect_injection` params
- `litellm` as optional dependency: `pip install nfo[llm]`

### Changed

- `pyproject.toml`: added `[llm]` and `[all]` optional dependency groups

## [0.1.12] - 2026-02-11

### Added

- **`configure()`** — one-liner project-wide logging setup with sink specs and stdlib bridge
- **`@logged`** — class decorator that auto-wraps all public methods with `@log_call`
- **`@skip`** — exclude specific methods from `@logged`
- **`_StdlibBridge`** — forwards stdlib `logging.getLogger()` records to nfo sinks
- `import nfo.setup` — zero-config auto-setup on import
- Example scripts: `basic_usage.py`, `sqlite_sink.py`, `csv_sink.py`, `markdown_sink.py`, `multi_sink.py`
- Integration modules for pactown (`nfo_config.py`) and pactown-com (`nfo_config.py`)

## [0.1.11] - 2026-02-11

### Changed

- Renamed package from `lg` to `nfo` (PyPI: `pip install nfo`)
- Updated all imports, tests, and packaging from `lg` to `nfo`

## [0.1.1] - 2026-02-11

### Added

- Initial release
- **`@log_call`** — decorator that logs function entry/exit, args, types, return value, exceptions, duration
- **`@catch`** — like `@log_call` but suppresses exceptions (returns configurable default)
- **`Logger`** — central dispatcher with multiple sinks + optional stdlib forwarding
- **`SQLiteSink`** — persist logs to SQLite database (queryable)
- **`CSVSink`** — append logs to CSV file
- **`MarkdownSink`** — write human-readable Markdown log files
- `LogEntry` dataclass with full function call metadata
- Thread-safe sinks with locks
- Zero external dependencies (stdlib only for core)
