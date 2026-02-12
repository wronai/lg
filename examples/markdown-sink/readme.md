# Markdown Sink

Logs function calls to a human-readable Markdown file — great for documentation and code reviews.

## What it shows

- **`MarkdownSink`** — write logs as a formatted Markdown table
- Readable output for sharing in PRs, wikis, or reports

## Run

```bash
pip install nfo
python examples/markdown-sink/main.py
```

## Key code

```python
from nfo import Logger, log_call, MarkdownSink

sink = MarkdownSink(file_path="logs.md")
logger = Logger(name="md-demo", sinks=[sink])

@log_call
def compute(x: float, y: float) -> float:
    return x ** y
```
