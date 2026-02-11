# Changelog

All notable changes to `nfo` are documented here.

## [Unreleased]

### Added

- **`auto_log()`** — one-call module-level patching: wraps all functions in a module with `@log_call` or `@catch` without individual decorators
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
