"""Click integration for nfo logging.

Provides NfoGroup (auto-logging Click group) and nfo_options decorator
for adding --nfo-sink, --nfo-format, --nfo-level CLI options.
"""

from __future__ import annotations

import time
import traceback as tb
from typing import Any, Optional

import click

from nfo.models import LogEntry
from nfo.logger import Logger
from nfo.terminal import TerminalSink


class NfoGroup(click.Group):
    """Click Group that automatically logs every command invocation via nfo.

    Usage::

        @click.group(cls=NfoGroup)
        @nfo_options
        def cli(**kwargs):
            pass
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._nfo_logger: Optional[Logger] = kwargs.pop("nfo_logger", None)
        super().__init__(*args, **kwargs)

    def invoke(self, ctx: click.Context) -> Any:
        logger = self._resolve_logger(ctx)
        cmd_name = ctx.info_name or "unknown"
        start = time.perf_counter()

        try:
            result = super().invoke(ctx)
            duration = (time.perf_counter() - start) * 1000

            entry = LogEntry(
                timestamp=LogEntry.now(),
                level="INFO",
                function_name=f"cli.{cmd_name}",
                module="click",
                args=tuple(ctx.args) if ctx.args else (),
                kwargs={
                    k: v
                    for k, v in (ctx.params or {}).items()
                    if not k.startswith("nfo_")
                },
                arg_types=[],
                kwarg_types={},
                duration_ms=duration,
                return_value=None,
            )
            logger.emit(entry)
            return result

        except Exception as exc:
            duration = (time.perf_counter() - start) * 1000
            entry = LogEntry(
                timestamp=LogEntry.now(),
                level="ERROR",
                function_name=f"cli.{cmd_name}",
                module="click",
                args=tuple(ctx.args) if ctx.args else (),
                kwargs={
                    k: v
                    for k, v in (ctx.params or {}).items()
                    if not k.startswith("nfo_")
                },
                arg_types=[],
                kwarg_types={},
                duration_ms=duration,
                exception=str(exc),
                exception_type=type(exc).__name__,
                traceback=tb.format_exc(),
            )
            logger.emit(entry)
            raise

    def _resolve_logger(self, ctx: click.Context) -> Logger:
        """Get or create the nfo Logger from Click context."""
        obj = ctx.ensure_object(dict)
        logger = obj.get("nfo_logger") or self._nfo_logger

        if logger is None:
            sink_spec = ctx.params.get("nfo_sink", "")
            fmt = ctx.params.get("nfo_format", "color")
            level = ctx.params.get("nfo_level", "DEBUG")

            terminal = TerminalSink(format=fmt)
            logger = Logger(
                name="nfo-cli",
                level=level,
                sinks=[terminal],
                propagate_stdlib=False,
            )

            if sink_spec:
                from nfo.configure import _parse_sink_spec

                logger.add_sink(_parse_sink_spec(sink_spec))

            obj["nfo_logger"] = logger

        return logger


class NfoCommand(click.Command):
    """Click Command that logs its own invocation via nfo.

    Useful for standalone commands (not under NfoGroup)::

        @click.command(cls=NfoCommand)
        @nfo_options
        def deploy(nfo_sink, nfo_format, nfo_level, **kwargs):
            pass
    """

    def invoke(self, ctx: click.Context) -> Any:
        obj = ctx.ensure_object(dict)
        logger = obj.get("nfo_logger")

        if logger is None:
            sink_spec = ctx.params.get("nfo_sink", "")
            fmt = ctx.params.get("nfo_format", "color")
            level = ctx.params.get("nfo_level", "DEBUG")

            terminal = TerminalSink(format=fmt)
            logger = Logger(
                name="nfo-cli",
                level=level,
                sinks=[terminal],
                propagate_stdlib=False,
            )

            if sink_spec:
                from nfo.configure import _parse_sink_spec

                logger.add_sink(_parse_sink_spec(sink_spec))

            obj["nfo_logger"] = logger

        cmd_name = ctx.info_name or "unknown"
        start = time.perf_counter()

        try:
            result = super().invoke(ctx)
            duration = (time.perf_counter() - start) * 1000

            entry = LogEntry(
                timestamp=LogEntry.now(),
                level="INFO",
                function_name=cmd_name,
                module="click",
                args=(),
                kwargs={
                    k: v
                    for k, v in (ctx.params or {}).items()
                    if not k.startswith("nfo_")
                },
                arg_types=[],
                kwarg_types={},
                duration_ms=duration,
                return_value=None,
            )
            logger.emit(entry)
            return result

        except Exception as exc:
            duration = (time.perf_counter() - start) * 1000
            entry = LogEntry(
                timestamp=LogEntry.now(),
                level="ERROR",
                function_name=cmd_name,
                module="click",
                args=(),
                kwargs={
                    k: v
                    for k, v in (ctx.params or {}).items()
                    if not k.startswith("nfo_")
                },
                arg_types=[],
                kwarg_types={},
                duration_ms=duration,
                exception=str(exc),
                exception_type=type(exc).__name__,
                traceback=tb.format_exc(),
            )
            logger.emit(entry)
            raise


def nfo_options(func: Any) -> Any:
    """Decorator that adds common nfo CLI options to a Click command/group.

    Options added:
    - ``--nfo-sink``: sink spec (sqlite:logs.db, csv:logs.csv, md:logs.md)
    - ``--nfo-format``: terminal log format (ascii/color/markdown/toon/table)
    - ``--nfo-level``: minimum log level (DEBUG/INFO/WARNING/ERROR)
    """
    func = click.option(
        "--nfo-sink",
        default="",
        envvar="NFO_SINK",
        help="nfo sink spec (sqlite:logs.db, csv:logs.csv, md:logs.md)",
    )(func)
    func = click.option(
        "--nfo-format",
        default="color",
        type=click.Choice(["ascii", "color", "markdown", "toon", "table"]),
        envvar="NFO_FORMAT",
        help="Terminal log format",
    )(func)
    func = click.option(
        "--nfo-level",
        default="DEBUG",
        type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
        envvar="NFO_LEVEL",
        help="Minimum log level",
    )(func)
    return func
