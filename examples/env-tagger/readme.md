# EnvTagger + DynamicRouter + DiffTracker

Advanced multi-environment log correlation, dynamic sink routing, and version diff tracking.

## What it shows

- **`EnvTagger`** — auto-tags every log entry with environment, trace_id, version
- **`DynamicRouter`** — routes logs to different sinks based on rules (prod → SQLite, ci → CSV, errors → separate DB)
- **`DiffTracker`** — detects when a function's output changes between versions

## Run

```bash
pip install nfo
python examples/env-tagger/main.py
```

## Key code

### EnvTagger
```python
from nfo import EnvTagger, SQLiteSink, Logger

sink = EnvTagger(
    SQLiteSink("logs.db"),
    environment="prod",
    trace_id="req-abc-123",
    version="1.2.3",
)
logger = Logger(name="app", sinks=[sink])
```

### DynamicRouter
```python
from nfo import DynamicRouter, SQLiteSink, CSVSink, MarkdownSink

router = DynamicRouter(
    rules=[
        (lambda e: e.environment == "prod", SQLiteSink("prod.db")),
        (lambda e: e.environment == "ci", CSVSink("ci.csv")),
        (lambda e: e.level == "ERROR", SQLiteSink("errors.db")),
    ],
    default=MarkdownSink("dev.md"),
)
```

### DiffTracker
```python
from nfo import DiffTracker, SQLiteSink

sink = DiffTracker(SQLiteSink("diff.db"))
# Detects: v1.2.1 add(1,2)→3 vs v1.2.2 add(1,2)→4 [DIFF]
```
