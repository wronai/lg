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
_last_logger: Optional["Logger"] = None
_global_meta_policy: Optional[Any] = None
_global_auto_extract_meta: bool = False


def get_global_meta_policy() -> Optional[Any]:
    """Return the globally configured :class:`~nfo.meta.ThresholdPolicy` (if any)."""
    return _global_meta_policy


def get_global_auto_extract_meta() -> bool:
    """Return ``True`` if ``auto_extract_meta`` was enabled via :func:`configure`."""
    return _global_auto_extract_meta


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
    elif sink_type == "terminal":
        from nfo.terminal import TerminalSink
        fmt = path if path in ("ascii", "color", "markdown", "toon", "table") else "color"
        return TerminalSink(format=fmt)
    elif sink_type in ("json", "jsonl"):
        from nfo.json_sink import JSONSink
        return JSONSink(file_path=path)
    elif sink_type == "prometheus":
        from nfo.prometheus import PrometheusSink
        port = int(path) if path else 9090
        return PrometheusSink(port=port)
    else:
        raise ValueError(
            f"Unknown sink type '{sink_type}'. Supported: sqlite, csv, md, terminal, json, prometheus"
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

        message = record.getMessage()
        func = record.funcName or ""
        # Build a qualified function reference for better traceability
        if record.name and func and func not in ("", "<module>"):
            qualified = f"{record.name}.{func}"
        else:
            qualified = record.name or func

        entry = LogEntry(
            timestamp=LogEntry.now(),
            level=record.levelname,
            function_name=qualified,
            module=record.name,
            args=(),
            kwargs={},
            arg_types=[],
            kwarg_types={},
            return_value=message,
            return_type="str",
            exception=str(record.exc_info[1]) if record.exc_info and record.exc_info[1] else None,
            exception_type=type(record.exc_info[1]).__name__ if record.exc_info and record.exc_info[1] else None,
            traceback=self.format(record) if record.exc_info else None,
            duration_ms=None,
            extra={"message": message, "source": "stdlib_bridge"},
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
    environment: Optional[str] = None,
    version: Optional[str] = None,
    llm_model: Optional[str] = None,
    detect_injection: bool = False,
    force: bool = False,
    meta_policy: Optional[Any] = None,
    auto_extract_meta: bool = False,
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
        environment: Environment tag (auto-detected if None and env tagging enabled).
        version: App version tag (auto-detected if None and env tagging enabled).
        llm_model: litellm model for LLM-powered log analysis (e.g. "gpt-4o-mini").
                   Wraps sinks with LLMSink. Requires: pip install nfo[llm]
        detect_injection: Enable prompt injection detection in log args.
        meta_policy: :class:`~nfo.meta.ThresholdPolicy` for binary metadata
                     extraction. Stored globally for use by ``@log_call``
                     and ``@meta_log`` when no per-decorator policy is given.
        auto_extract_meta: If ``True``, enable metadata extraction globally.
                           Equivalent to ``NFO_META_EXTRACT=true``.

    Returns:
        Configured Logger instance.

    Environment variables (override arguments):
        NFO_LEVEL: Override log level
        NFO_SINKS: Comma-separated sink specs (e.g. "sqlite:logs.db,csv:logs.csv")
        NFO_ENV: Override environment tag
        NFO_LLM_MODEL: Override LLM model
        NFO_META_THRESHOLD: Override meta_policy max_arg_bytes (in bytes)
        NFO_META_EXTRACT: Set to 'true' to enable auto_extract_meta globally

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

        # Full pipeline: env tagging + LLM analysis + injection detection:
        configure(
            sinks=["sqlite:app.db"],
            environment="prod",
            llm_model="gpt-4o-mini",
            detect_injection=True,
        )

        # With binary metadata extraction:
        configure(
            sinks=["sqlite:app.db"],
            meta_policy=ThresholdPolicy(max_arg_bytes=4096),
            auto_extract_meta=True,
        )
    """
    global _configured, _last_logger, _global_meta_policy, _global_auto_extract_meta

    if _configured and not force and _last_logger is not None:
        return _last_logger

    # Environment overrides
    env_level = os.environ.get(f"{env_prefix}LEVEL")
    if env_level:
        level = env_level.upper()

    env_sinks = os.environ.get(f"{env_prefix}SINKS")

    # Environment overrides for new features
    env_env = os.environ.get(f"{env_prefix}ENV")
    if env_env:
        environment = env_env
    env_llm = os.environ.get(f"{env_prefix}LLM_MODEL")
    if env_llm:
        llm_model = env_llm

    # Meta extraction env overrides
    env_meta_extract = os.environ.get(f"{env_prefix}META_EXTRACT", "").lower()
    if env_meta_extract in ("true", "1", "yes"):
        auto_extract_meta = True
    env_meta_threshold = os.environ.get(f"{env_prefix}META_THRESHOLD")
    if env_meta_threshold:
        from nfo.meta import ThresholdPolicy
        threshold = int(env_meta_threshold)
        if meta_policy is None:
            meta_policy = ThresholdPolicy(max_arg_bytes=threshold, max_return_bytes=threshold)
        else:
            meta_policy.max_arg_bytes = threshold
            meta_policy.max_return_bytes = threshold

    # Store global meta policy and auto_extract flag
    _global_meta_policy = meta_policy
    _global_auto_extract_meta = auto_extract_meta

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

    # Wrap sinks with LLM analysis if model specified
    if llm_model and resolved_sinks:
        from nfo.llm import LLMSink
        resolved_sinks = [
            LLMSink(
                model=llm_model,
                delegate=sink,
                async_mode=True,
                detect_injection=detect_injection,
            )
            for sink in resolved_sinks
        ]
    elif detect_injection and resolved_sinks:
        from nfo.llm import LLMSink
        resolved_sinks = [
            LLMSink(
                model="",
                delegate=sink,
                async_mode=False,
                detect_injection=True,
                analyze_levels=[],
            )
            for sink in resolved_sinks
        ]

    # Wrap sinks with env tagging if environment or version specified
    if (environment or version) and resolved_sinks:
        from nfo.env import EnvTagger
        resolved_sinks = [
            EnvTagger(
                sink,
                environment=environment,
                version=version,
                auto_detect=True,
            )
            for sink in resolved_sinks
        ]

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
            # Sort so parents come before children (shorter names first).
            # Only attach bridge to a logger if no ancestor in the list
            # already has it — stdlib propagation handles children.
            bridged: set[str] = set()
            for mod in sorted(modules, key=len):
                has_ancestor = any(
                    mod.startswith(anc + ".") for anc in bridged
                )
                mod_logger = logging.getLogger(mod)
                if not has_ancestor:
                    if bridge not in mod_logger.handlers:
                        mod_logger.addHandler(bridge)
                    bridged.add(mod)

    _configured = True
    _last_logger = logger
    return logger
