# Auto-Log

Zero-decorator module-wide logging with `auto_log()` — patches all public functions in a module with a single call.

## What it shows

- **`auto_log()`** — wraps every public function in the current module with `@log_call`
- **`@skip`** — explicitly exclude specific functions from auto-logging
- Private functions (`_prefixed`) are skipped automatically

## Run

```bash
pip install nfo
python examples/auto-log/main.py
```

## Key code

```python
from nfo import configure, auto_log, skip

configure(sinks=["sqlite:logs.db"])

def create_user(name: str, email: str) -> dict:
    return {"name": name, "email": email, "id": 1001}

@skip
def health_check() -> str:
    return "ok"  # not logged

auto_log()  # patches all public functions above
```

No `@log_call` on every function — one call does it all.
