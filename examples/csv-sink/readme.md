# CSV Sink

Logs function calls to a CSV file — easy to open in Excel, import to Pandas, or pipe to other tools.

## What it shows

- **`CSVSink`** — append log entries to a CSV file
- CSV output with all fields (timestamp, level, function, args, return value, duration)

## Run

```bash
pip install nfo
python examples/csv-sink/main.py
```

## Key code

```python
from nfo import Logger, log_call, CSVSink

sink = CSVSink(file_path="logs.csv")
logger = Logger(name="csv-demo", sinks=[sink])

@log_call
def multiply(a: int, b: int) -> int:
    return a * b
```
