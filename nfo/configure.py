"""
Project-level configuration for nfo.

Provides `configure()` — a single function to set up structured logging
across an entire project. Follows the Open/Closed Principle: extend via
custom sinks without modifying core code.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from nfo.logger import Logger
from nfo.sinks import CSVSink, MarkdownSink, SQLiteSink, Sink
from nfo.decorators import set_default_logger

_configured = False


def _parse_sink_spec(spec: str) -> Sink:
    """Parse a sink specification string like 'sqlite:logs.db' or 'csv:logs.csv'."""
    if ":" not in spec:
        raise ValueError(
            f"Invalid sink spec '{spec}'. Use format 'type:path' "
            f"(e.g. 'sqlite:logs.db', 'csv:logs.csv', 'md:logs.md')"
        )
    sink_type, path = spec.split(":", 1)
    sink_type = sink_type.strip().lower()
    path = path.strip()

    if sink_type in ("sqlite", "db"):
        return SQLiteSink(db_path=path)
    elif sink_type == "csv":
        return CSVSink(file_path=path)
    elif sink_type in ("md", "markdown"):
        return MarkdownSink(file_path=path)
    else:
        raise ValueError(
            f"Unknown sink type '{sink_type}'. Supported: sqlite, csv, md"
        )


class _StdlibBridge(logging.Handler):
    """
    Bridge that intercepts stdlib logging records and forwards them
    to nfo sinks. This allows existing `logging.getLogger(__name__)`
    calls to automatically write to SQLite/CSV/Markdown.

    Follows the Liskov Substitution Principle — works as a drop-in
    logging.Handler.
    """

    def __init__(self, nfo_logger: Logger) -> None:
        super().__init__()
        self._nfo_logger = nfo_logger

    def emit(self, record: logging.LogRecord) -> None:
        from nfo.models import LogEntry

        entry = LogEntry(
            timestamp=LogEntry.now(),
            level=record.levelname,
            function_name=record.funcName or "",
            module=record.name,
            args=(),
            kwargs={},
            arg_types=[],
            kwarg_types={},
            return_value=None,
            return_type=None,
            exception=str(record.exc_info[1]) if record.exc_info and record.exc_info[1] else None,
            exception_type=type(record.exc_info[1]).__name__ if record.exc_info and record.exc_info[1] else None,
            traceback=self.format(record) if record.exc_info else None,
            duration_ms=None,
            extra={"message": record.getMessage()},
        )
        for sink in self._nfo_logger._sinks:
            try:
                sink.write(entry)
            except Exception:
                pass


def configure(
    *,
    name: str = "nfo",
    level: str = "DEBUG",
    sinks: Optional[Sequence[Union[str, Sink]]] = None,
    modules: Optional[Sequence[str]] = None,
    bridge_stdlib: bool = False,
    propagate_stdlib: bool = True,
    env_prefix: str = "NFO_",
) -> Logger:
    """
    Configure nfo logging for the entire project.

    Args:
        name: Logger name (used for stdlib logger).
        level: Minimum log level (DEBUG, INFO, WARNING, ERROR).
        sinks: List of sink specs ('sqlite:path', 'csv:path', 'md:path')
               or Sink instances. If None, reads from NFO_SINKS env var.
        modules: stdlib logger names to bridge to nfo sinks.
                 If provided, attaches nfo handler to these loggers.
        bridge_stdlib: If True, attach nfo handler to the root logger
                       so ALL stdlib logging goes through nfo sinks.
        propagate_stdlib: Forward nfo decorator logs to stdlib (console).
        env_prefix: Prefix for environment variable overrides.

    Returns:
        Configured Logger instance.

    Environment variables (override arguments):
        NFO_LEVEL: Override log level
        NFO_SINKS: Comma-separated sink specs (e.g. "sqlite:logs.db,csv:logs.csv")

    Examples:
        # Zero-config (just console output):
        from nfo import configure
        configure()

        # With SQLite + CSV:
        configure(sinks=["sqlite:app.db", "csv:app.csv"])

        # Bridge existing stdlib loggers:
        configure(
            sinks=["sqlite:app.db"],
            modules=["pactown.sandbox", "pactown.runner"],
        )
    """
    global _configured

    # Environment overrides
    env_level = os.environ.get(f"{env_prefix}LEVEL")
    if env_level:
        level = env_level.upper()

    env_sinks = os.environ.get(f"{env_prefix}SINKS")

    # Build sink list
    resolved_sinks: List[Sink] = []
    if sinks is not None:
        for s in sinks:
            if isinstance(s, str):
                resolved_sinks.append(_parse_sink_spec(s))
            else:
                resolved_sinks.append(s)
    elif env_sinks:
        for spec in env_sinks.split(","):
            spec = spec.strip()
            if spec:
                resolved_sinks.append(_parse_sink_spec(spec))

    # Create logger
    logger = Logger(
        name=name,
        level=level,
        sinks=resolved_sinks,
        propagate_stdlib=propagate_stdlib,
    )
    set_default_logger(logger)

    # Bridge stdlib loggers to nfo sinks (if sinks are configured)
    if resolved_sinks and (bridge_stdlib or modules):
        bridge = _StdlibBridge(logger)
        bridge.setLevel(getattr(logging, level.upper(), logging.DEBUG))

        if bridge_stdlib:
            root = logging.getLogger()
            if bridge not in root.handlers:
                root.addHandler(bridge)

        if modules:
            for mod in modules:
                mod_logger = logging.getLogger(mod)
                if bridge not in mod_logger.handlers:
                    mod_logger.addHandler(bridge)

    _configured = True
    return logger
