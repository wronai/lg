# nfo

**Automatic function logging with decorators — output to SQLite, CSV, and Markdown.**

[![PyPI](https://img.shields.io/pypi/v/nfo)](https://pypi.org/project/nfo/)
[![Python](https://img.shields.io/pypi/pyversions/nfo)](https://pypi.org/project/nfo/)
[![License](https://img.shields.io/pypi/l/nfo)](LICENSE)

Zero-dependency Python package that automatically logs function calls using decorators.
Captures arguments, types, return values, exceptions, and execution time — writes to **SQLite**, **CSV**, or **Markdown**.

## Installation

```bash
pip install nfo
```

## Quick Start

```python
from nfo import log_call, catch

@log_call
def add(a: int, b: int) -> int:
    return a + b

@catch
def risky(x: float) -> float:
    return 1 / x

add(3, 7)       # logs: args, types, return value, duration
risky(0)        # logs exception, returns None (no crash)
```

Output (stderr):
```
2026-02-11 21:59:34 | DEBUG | nfo | add() | args=(3, 7) | -> 10 | [0.00ms]
2026-02-11 21:59:34 | ERROR | nfo | risky() | args=(0,) | EXCEPTION ZeroDivisionError: division by zero | [0.00ms]
```

## Features

- **`@log_call`** — logs entry/exit, args with types, return value, exceptions + traceback, duration
- **`@catch`** — like `@log_call` but suppresses exceptions (returns configurable default)
- **`SQLiteSink`** — persist logs to SQLite database
- **`CSVSink`** — append logs to CSV file
- **`MarkdownSink`** — write human-readable Markdown log files
- **`Logger`** — central dispatcher with multiple sinks + optional stdlib `logging` forwarding
- **Zero dependencies** — uses only Python standard library
- **Thread-safe** — all sinks use locks

## Sinks

### SQLite

```python
from nfo import Logger, log_call, SQLiteSink
from nfo.decorators import set_default_logger

logger = Logger(sinks=[SQLiteSink("logs.db")])
set_default_logger(logger)

@log_call
def fetch_user(user_id: int) -> dict:
    return {"id": user_id, "name": "Alice"}

fetch_user(42)
# Query: SELECT * FROM logs WHERE level = 'ERROR'
```

### CSV

```python
from nfo import Logger, log_call, CSVSink
from nfo.decorators import set_default_logger

logger = Logger(sinks=[CSVSink("logs.csv")])
set_default_logger(logger)

@log_call
def multiply(a: int, b: int) -> int:
    return a * b

multiply(6, 7)
```

### Markdown

```python
from nfo import Logger, log_call, MarkdownSink
from nfo.decorators import set_default_logger

logger = Logger(sinks=[MarkdownSink("logs.md")], propagate_stdlib=False)
set_default_logger(logger)

@log_call
def compute(x: float, y: float) -> float:
    return x ** y

compute(2.0, 10.0)
```

### Multiple Sinks

```python
from nfo import Logger, SQLiteSink, CSVSink, MarkdownSink

logger = Logger(sinks=[
    SQLiteSink("logs.db"),
    CSVSink("logs.csv"),
    MarkdownSink("logs.md"),
])
```

## What Gets Logged

Each `@log_call` / `@catch` captures:

| Field | Description |
|-------|-------------|
| `timestamp` | UTC ISO-8601 |
| `level` | DEBUG (success) or ERROR (exception) |
| `function_name` | Qualified function name |
| `module` | Python module |
| `args` / `kwargs` | Positional and keyword arguments |
| `arg_types` / `kwarg_types` | Type names of each argument |
| `return_value` / `return_type` | Return value and its type |
| `exception` / `exception_type` | Exception message and class |
| `traceback` | Full traceback on error |
| `duration_ms` | Wall-clock execution time |

## Examples

See the [`examples/`](examples/) directory:

- [`basic_usage.py`](examples/basic_usage.py) — `@log_call` and `@catch` basics
- [`sqlite_sink.py`](examples/sqlite_sink.py) — logging to SQLite + querying
- [`csv_sink.py`](examples/csv_sink.py) — logging to CSV
- [`markdown_sink.py`](examples/markdown_sink.py) — logging to Markdown
- [`multi_sink.py`](examples/multi_sink.py) — all three sinks at once

Run any example:
```bash
pip install nfo
python examples/basic_usage.py
```

## Development

```bash
git clone https://github.com/wronai/lg.git
cd lg
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```

## License

[Apache-2.0](LICENSE)