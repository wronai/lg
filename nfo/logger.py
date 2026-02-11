"""Central logger that dispatches log entries to configured sinks."""

from __future__ import annotations

import logging
import sys
from typing import List, Optional

from nfo.models import LogEntry
from nfo.sinks import Sink


class Logger:
    """
    Central logger instance.

    Collects :class:`LogEntry` objects from decorators and dispatches them
    to every registered :class:`Sink`.  It also optionally forwards messages
    to the standard-library ``logging`` module so they appear in the console.
    """

    def __init__(
        self,
        name: str = "nfo",
        level: str = "DEBUG",
        sinks: Optional[List[Sink]] = None,
        propagate_stdlib: bool = True,
    ) -> None:
        self.name = name
        self.level = level.upper()
        self._sinks: List[Sink] = list(sinks) if sinks else []
        self._stdlib_logger: Optional[logging.Logger] = None

        if propagate_stdlib:
            self._stdlib_logger = logging.getLogger(name)
            self._stdlib_logger.setLevel(getattr(logging, self.level, logging.DEBUG))
            if not self._stdlib_logger.handlers:
                handler = logging.StreamHandler(sys.stderr)
                handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
                    )
                )
                self._stdlib_logger.addHandler(handler)

    # -- sink management -----------------------------------------------------

    def add_sink(self, sink: Sink) -> "Logger":
        """Register a new sink and return *self* for chaining."""
        self._sinks.append(sink)
        return self

    def remove_sink(self, sink: Sink) -> None:
        self._sinks.remove(sink)

    # -- dispatching ---------------------------------------------------------

    def emit(self, entry: LogEntry) -> None:
        """Send a log entry to all sinks and (optionally) stdlib."""
        for sink in self._sinks:
            sink.write(entry)

        if self._stdlib_logger:
            lvl = getattr(logging, entry.level.upper(), logging.DEBUG)
            msg = self._format_stdlib(entry)
            self._stdlib_logger.log(lvl, msg)

    @staticmethod
    def _format_stdlib(entry: LogEntry) -> str:
        parts = [f"{entry.function_name}()"]
        if entry.args:
            parts.append(f"args={entry.args!r}")
        if entry.kwargs:
            parts.append(f"kwargs={entry.kwargs!r}")
        if entry.return_value is not None:
            parts.append(f"-> {entry.return_value!r}")
        if entry.exception:
            parts.append(f"EXCEPTION {entry.exception_type}: {entry.exception}")
        if entry.duration_ms is not None:
            parts.append(f"[{entry.duration_ms:.2f}ms]")
        return " | ".join(parts)

    # -- lifecycle -----------------------------------------------------------

    def close(self) -> None:
        """Close all sinks."""
        for sink in self._sinks:
            sink.close()
