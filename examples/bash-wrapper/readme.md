# Bash Wrapper

Run any shell script through nfo logging — captures args, stdout/stderr, return code, and duration to SQLite.

## What it shows

- **`@log_call` on subprocess** — wraps `subprocess.run()` with full nfo logging
- Captures stdout, stderr, return code, and execution time
- Works with any executable: Bash, Python, Make, Docker, etc.

## Run

```bash
pip install nfo
python examples/bash-wrapper/main.py echo "Hello from nfo-bash"
python examples/bash-wrapper/main.py ls -la
python examples/bash-wrapper/main.py ./deploy.sh prod
```

## Output

```
2026-02-12 | DEBUG | nfo-bash | run_bash() | args=('echo', 'Hello') | -> {...} | [2.38ms]
Hello from nfo-bash
```

## Key code

```python
from nfo import log_call, Logger, SQLiteSink

logger = Logger(name="nfo-bash", sinks=[SQLiteSink("bash_logs.db")])

@log_call
def run_bash(cmd, *args):
    result = subprocess.run([cmd, *args], capture_output=True, text=True)
    return {"stdout": result.stdout, "returncode": result.returncode}
```
