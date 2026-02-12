# Multi-Sink

Logs function calls to **all three sinks at once**: SQLite + CSV + Markdown.

## What it shows

- **Multiple sinks** — a single `Logger` writing to SQLite, CSV, and Markdown simultaneously
- Each call is logged to all sinks atomically

## Run

```bash
pip install nfo
python examples/multi-sink/main.py
```

## Key code

```python
from nfo import Logger, log_call, SQLiteSink, CSVSink, MarkdownSink

logger = Logger(
    name="multi-demo",
    sinks=[
        SQLiteSink(db_path="logs.db"),
        CSVSink(file_path="logs.csv"),
        MarkdownSink(file_path="logs.md"),
    ],
)

@log_call
def fibonacci(n: int) -> int:
    ...
```
