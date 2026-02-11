#!/usr/bin/env python3
"""nfo example — logging to Markdown file."""

from pathlib import Path

from nfo import Logger, log_call, catch, MarkdownSink
from nfo.decorators import set_default_logger

MD_PATH = Path(__file__).parent / "demo_logs.md"


def setup_logger() -> Logger:
    sink = MarkdownSink(file_path=MD_PATH)
    logger = Logger(name="md-demo", sinks=[sink], propagate_stdlib=False)
    set_default_logger(logger)
    return logger


@log_call
def compute(x: float, y: float) -> float:
    return x ** y


@catch
def dangerous(data: str) -> dict:
    import json
    return json.loads(data)


if __name__ == "__main__":
    logger = setup_logger()

    compute(2.0, 10.0)
    compute(3.14, 2.0)
    dangerous("not json")
    dangerous('{"ok": true}')

    logger.close()

    print(f"Logs written to: {MD_PATH}")
    print()
    print(MD_PATH.read_text())

    # Cleanup
    MD_PATH.unlink(missing_ok=True)
