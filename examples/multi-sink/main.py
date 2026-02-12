#!/usr/bin/env python3
"""nfo example — multiple sinks at once (SQLite + CSV + Markdown)."""

from pathlib import Path

from nfo import Logger, log_call, catch, SQLiteSink, CSVSink, MarkdownSink
from nfo.decorators import set_default_logger

OUT = Path(__file__).parent

DB_PATH = OUT / "multi_logs.db"
CSV_PATH = OUT / "multi_logs.csv"
MD_PATH = OUT / "multi_logs.md"


def setup_logger() -> Logger:
    logger = Logger(
        name="multi-demo",
        sinks=[
            SQLiteSink(db_path=DB_PATH),
            CSVSink(file_path=CSV_PATH),
            MarkdownSink(file_path=MD_PATH),
        ],
        propagate_stdlib=True,
    )
    set_default_logger(logger)
    return logger


@log_call
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


@log_call(level="INFO")
def batch_process(items: list) -> dict:
    return {"processed": len(items), "status": "ok"}


@catch(default="ERROR")
def parse_int(value: str) -> int:
    return int(value)


if __name__ == "__main__":
    logger = setup_logger()

    fibonacci(10)
    fibonacci(20)
    batch_process(["task1", "task2", "task3"])
    parse_int("42")
    parse_int("not_a_number")

    logger.close()

    print(f"SQLite: {DB_PATH}")
    print(f"CSV:    {CSV_PATH}")
    print(f"MD:     {MD_PATH}")
    print()
    print("--- CSV content ---")
    print(CSV_PATH.read_text())

    # Cleanup
    for p in (DB_PATH, CSV_PATH, MD_PATH):
        p.unlink(missing_ok=True)
