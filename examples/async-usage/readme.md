# Async Usage

Demonstrates transparent async support — `@log_call` and `@catch` automatically detect `async def` functions.

## What it shows

- **Async `@log_call`** — works with `async def` without a separate decorator
- **Async `@catch`** — suppresses exceptions in async functions
- **`asyncio.gather`** — concurrent execution, all calls logged

## Run

```bash
pip install nfo
python examples/async-usage/main.py
```

## Key code

```python
from nfo import log_call, catch

@log_call
async def fetch_data(url: str) -> dict:
    await asyncio.sleep(0.05)
    return {"url": url, "status": 200}

@catch(default={})
async def risky_fetch(url: str) -> dict:
    if "bad" in url:
        raise ConnectionError(f"Cannot connect to {url}")
    return {"url": url, "data": "ok"}
```

No special async decorator needed — nfo detects `async def` via `inspect.iscoroutinefunction()`.
