#!/usr/bin/env python3
"""
nfo example — Bash wrapper (nfo-bash proxy).

Runs any shell script through nfo logging, capturing args, stdout/stderr,
return code, and execution duration into SQLite.

Usage:
    # Save as nfo-bash, chmod +x, then:
    ./nfo-bash ./deploy.sh prod
    ./nfo-bash ./backup.sh --date 2026-02-12

    # Or run directly:
    python examples/bash_wrapper.py ./myscript.sh arg1 arg2

All invocations are logged to bash_logs.db with full nfo metadata.
"""

import os
import subprocess
import sys
from pathlib import Path

from nfo import Logger, SQLiteSink, CSVSink, log_call
from nfo.decorators import set_default_logger

DB_PATH = Path(__file__).parent / "bash_logs.db"
CSV_PATH = Path(__file__).parent / "bash_logs.csv"


def setup_logger() -> Logger:
    logger = Logger(
        name="nfo-bash",
        sinks=[
            SQLiteSink(db_path=DB_PATH),
            CSVSink(file_path=CSV_PATH),
        ],
        propagate_stdlib=True,
    )
    set_default_logger(logger)
    return logger


@log_call
def run_bash(script_path: str, *args, env=None) -> dict:
    """Run a Bash script and capture its output through nfo logging."""
    cmd = [script_path, *args]
    result = subprocess.run(
        cmd, capture_output=True, text=True, env=env or os.environ
    )
    return {
        "cmd": cmd,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
        "success": result.returncode == 0,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: nfo-bash <script> [args...]")
        print()
        print("Examples:")
        print("  nfo-bash ./deploy.sh prod")
        print("  nfo-bash ./backup.sh --date 2026-02-12")
        print()
        print("Logs are written to bash_logs.db and bash_logs.csv")
        sys.exit(1)

    logger = setup_logger()
    result = run_bash(*sys.argv[1:])

    print(result["stdout"], end="")
    if result["stderr"]:
        print(result["stderr"], end="", file=sys.stderr)

    logger.close()
    sys.exit(result["returncode"])


if __name__ == "__main__":
    main()
