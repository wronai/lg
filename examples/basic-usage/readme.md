# Basic Usage

Demonstrates the core nfo decorators: `@log_call` and `@catch`.

## What it shows

- **`@log_call`** — automatically logs function args, return value, duration, and exceptions
- **`@catch`** — like `@log_call` but suppresses exceptions, returns a default value instead

## Run

```bash
pip install nfo
python examples/basic-usage/main.py
```

## Output

```
=== @log_call ===
add(3, 7) = 10

greet('nfo') = Hello, nfo!

=== @catch (suppresses exceptions) ===
risky_divide(10, 0) = None  (no crash!)

risky_divide(10, 3) = 3.3333333333333335
```

## Key code

```python
from nfo import log_call, catch

@log_call
def add(a: int, b: int) -> int:
    return a + b

@catch
def risky_divide(a: float, b: float) -> float:
    return a / b  # returns None on ZeroDivisionError
```
