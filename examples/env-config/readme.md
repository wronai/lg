# .env Configuration

Load nfo settings from a `.env` file using `python-dotenv` — zero hardcoded config in code.

## What it shows

- **`python-dotenv`** loads `.env` into `os.environ` before `configure()`
- **`configure()`** reads `NFO_LEVEL`, `NFO_SINKS`, `NFO_ENV`, etc. automatically
- All settings come from `.env` — switch environments by swapping the file

## Setup

```bash
pip install nfo python-dotenv

# Copy template and adjust:
cp examples/.env.example examples/.env
```

## Run

```bash
python examples/env-config/main.py
```

## Key code

```python
from dotenv import load_dotenv
load_dotenv()  # loads .env → os.environ

from nfo import configure, log_call
configure()  # reads NFO_LEVEL, NFO_SINKS, NFO_ENV automatically

@log_call
def create_order(order_id: str, amount: float) -> dict:
    return {"order_id": order_id, "status": "created"}
```

## Environment variables

See [`../.env.example`](../.env.example) for all available `NFO_*` variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `NFO_LEVEL` | Log level | `DEBUG` |
| `NFO_SINKS` | Sink specs (comma-separated) | console |
| `NFO_ENV` | Environment tag | auto-detect |
| `NFO_VERSION` | App version | auto-detect |
| `NFO_LOG_DIR` | Log directory | `./logs` |
| `NFO_LLM_MODEL` | LLM model for analysis | — |
