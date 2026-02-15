#!/usr/bin/env python3
"""Demo showing all 5 terminal output formats side by side.

Usage:
    python demo_formats.py
"""

import io
from datetime import datetime, timezone

from nfo.models import LogEntry
from nfo.terminal import TerminalSink


def make_entry(
    function_name="deploy",
    args=("prod",),
    kwargs=None,
    return_value=None,
    duration_ms=2300.0,
    exception=None,
    exception_type=None,
):
    return LogEntry(
        timestamp=datetime(2026, 2, 15, 9, 30, 23, tzinfo=timezone.utc),
        level="ERROR" if exception else "DEBUG",
        function_name=function_name,
        module="myapp",
        args=args,
        kwargs=kwargs or {"force": True},
        arg_types=[type(a).__name__ for a in args],
        kwarg_types={},
        return_value=return_value,
        duration_ms=duration_ms,
        exception=exception,
        exception_type=exception_type,
        extra={},
    )


def demo():
    success = make_entry(return_value={"status": "ok"})
    error = make_entry(
        function_name="rollback",
        args=("prod",),
        kwargs={},
        return_value=None,
        duration_ms=500,
        exception="connection refused",
        exception_type="ConnectionError",
    )

    for fmt in ("ascii", "color", "markdown", "toon", "table"):
        print(f"\n{'='*60}")
        print(f"  Format: {fmt}")
        print(f"{'='*60}\n")

        sink = TerminalSink(format=fmt, stream=io.StringIO())
        # Write to both StringIO (for capture) and stdout
        import sys
        sink_stdout = TerminalSink(format=fmt, stream=sys.stdout)

        print("  [success]")
        sink_stdout.write(success)

        print("  [error]")
        sink_stdout.write(error)


if __name__ == "__main__":
    demo()
