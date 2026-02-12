#!/usr/bin/env python3
"""
nfo example — EnvTagger + DynamicRouter for multi-environment logging.

Demonstrates:
- EnvTagger: auto-tag logs with environment/trace_id/version
- DynamicRouter: route logs to different sinks by env/level
- DiffTracker: detect output changes between function versions

Usage:
    python examples/env_tagger_usage.py
"""

from pathlib import Path

from nfo import (
    Logger,
    log_call,
    catch,
    SQLiteSink,
    CSVSink,
    MarkdownSink,
    EnvTagger,
    DynamicRouter,
    DiffTracker,
)
from nfo.decorators import set_default_logger

OUT = Path(__file__).parent
PROD_DB = OUT / "prod_logs.db"
CI_CSV = OUT / "ci_logs.csv"
ERRORS_DB = OUT / "errors.db"
DEV_MD = OUT / "dev_logs.md"


def demo_env_tagger():
    """EnvTagger wraps a sink to auto-tag every log entry."""
    print("=== EnvTagger ===")

    sink = EnvTagger(
        SQLiteSink(db_path=PROD_DB),
        environment="prod",
        trace_id="req-abc-123",
        version="1.2.3",
    )
    logger = Logger(name="env-demo", sinks=[sink], propagate_stdlib=True)
    set_default_logger(logger)

    @log_call
    def create_user(name: str) -> dict:
        return {"name": name, "id": 42}

    create_user("Alice")
    logger.close()

    # Show tagged logs
    import sqlite3
    conn = sqlite3.connect(str(PROD_DB))
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM logs ORDER BY timestamp DESC LIMIT 1").fetchone()
    if row:
        d = dict(row)
        print(f"  function: {d.get('function_name', 'N/A')}")
        print(f"  environment: {d.get('environment', 'N/A')}")
        print(f"  trace_id: {d.get('trace_id', 'N/A')}")
        print(f"  version: {d.get('version', 'N/A')}")
    conn.close()
    print()


def demo_dynamic_router():
    """DynamicRouter sends logs to different sinks based on rules."""
    print("=== DynamicRouter ===")

    router = DynamicRouter(
        rules=[
            (lambda e: getattr(e, 'environment', '') == "prod", SQLiteSink(PROD_DB)),
            (lambda e: getattr(e, 'environment', '') == "ci", CSVSink(CI_CSV)),
            (lambda e: e.level == "ERROR", SQLiteSink(ERRORS_DB)),
        ],
        default=MarkdownSink(DEV_MD),
    )
    logger = Logger(name="router-demo", sinks=[router], propagate_stdlib=True)
    set_default_logger(logger)

    @log_call
    def process(x: int) -> int:
        return x * 2

    @catch(default=None)
    def risky(x: int) -> float:
        return 1 / x

    process(10)
    risky(0)  # ERROR → routed to errors.db

    logger.close()
    print("  Logs routed to different sinks based on level/environment")
    print()


def demo_diff_tracker():
    """DiffTracker detects when function output changes."""
    print("=== DiffTracker ===")

    diff_db = OUT / "diff_logs.db"
    sink = DiffTracker(SQLiteSink(diff_db))
    logger = Logger(name="diff-demo", sinks=[sink], propagate_stdlib=True)
    set_default_logger(logger)

    @log_call
    def compute(x: int, y: int) -> int:
        return x + y

    compute(1, 2)
    compute(1, 2)  # same args → DiffTracker tracks consistency

    logger.close()
    print("  DiffTracker monitors output consistency across calls")
    diff_db.unlink(missing_ok=True)
    print()


if __name__ == "__main__":
    demo_env_tagger()
    demo_dynamic_router()
    demo_diff_tracker()

    # Cleanup
    for p in (PROD_DB, CI_CSV, ERRORS_DB, DEV_MD):
        p.unlink(missing_ok=True)

    print("Done. All demo files cleaned up.")
