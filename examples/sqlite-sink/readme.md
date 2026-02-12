# SQLite Sink

Logs function calls to a queryable SQLite database.

## What it shows

- **`SQLiteSink`** — persist all log entries to SQLite
- Querying logs with standard SQL after execution

## Run

```bash
pip install nfo
python examples/sqlite-sink/main.py
```

## Output

```
User: {'id': 42, 'name': 'Alice', 'role': 'admin'}
Config: {'debug': True}
Bad config (caught): {}
ValueError caught (logged to SQLite)

--- Logs in demo_logs.db ---
  2026-02-12T10:00:00 | DEBUG | fetch_user | ret={'id': 42, ...}   | exc=
  2026-02-12T10:00:00 | DEBUG | parse_config | ret={'debug': True}  | exc=
  2026-02-12T10:00:00 | ERROR | parse_config | ret=                 | exc=Expecting value...
  2026-02-12T10:00:00 | ERROR | fetch_user  | ret=                  | exc=Invalid user_id: -1
```

## Key code

```python
from nfo import Logger, log_call, SQLiteSink

sink = SQLiteSink(db_path="logs.db")
logger = Logger(name="my-app", sinks=[sink])

@log_call
def fetch_user(user_id: int) -> dict:
    return {"id": user_id, "name": "Alice"}
```
