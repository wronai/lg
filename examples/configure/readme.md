# Configure

One-liner project-wide setup with `configure()` — replaces manual Logger + Sink + set_default_logger.

## What it shows

- **`configure()`** — set sinks, environment, version, and stdlib bridge in one call
- **Sink specs as strings** — `"sqlite:path"`, `"csv:path"`, `"md:path"`
- **`@logged` class decorator** — auto-wrap all public methods

## Run

```bash
pip install nfo
python examples/configure/main.py
```

## Key code

```python
from nfo import configure, log_call, catch, logged

configure(
    name="my-app",
    sinks=["sqlite:app.db", "csv:app.csv"],
    environment="dev",
    version="1.0.0",
)

@log_call
def process_order(order_id: str, amount: float) -> dict:
    return {"order_id": order_id, "status": "completed"}

@logged
class PaymentService:
    def charge(self, amount: float) -> bool:
        return amount > 0
```

All decorators automatically use the configured sinks — no manual Logger wiring.
