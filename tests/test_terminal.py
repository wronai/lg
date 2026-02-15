"""Tests for nfo.terminal — TerminalSink with 5 output formats."""

import io
from datetime import datetime, timezone

import pytest

from nfo.models import LogEntry
from nfo.terminal import TerminalSink


def _make_entry(
    level="DEBUG",
    function_name="add",
    args=(3, 7),
    kwargs=None,
    return_value=10,
    duration_ms=1.5,
    exception=None,
    exception_type=None,
    traceback=None,
    extra=None,
):
    return LogEntry(
        timestamp=datetime(2026, 2, 15, 9, 30, 23, tzinfo=timezone.utc),
        level=level,
        function_name=function_name,
        module="test",
        args=args,
        kwargs=kwargs or {},
        arg_types=[type(a).__name__ for a in args],
        kwarg_types={},
        return_value=return_value,
        duration_ms=duration_ms,
        exception=exception,
        exception_type=exception_type,
        traceback=traceback,
        extra=extra or {},
    )


# ---------------------------------------------------------------------------
# ASCII format
# ---------------------------------------------------------------------------

class TestAsciiFormat:

    def test_basic_output(self):
        buf = io.StringIO()
        sink = TerminalSink(format="ascii", stream=buf)
        sink.write(_make_entry())
        out = buf.getvalue()
        assert "09:30:23" in out
        assert "DEBUG" in out
        assert "add()" in out
        assert "-> 10" in out
        assert "[1.5ms]" in out

    def test_exception_output(self):
        buf = io.StringIO()
        sink = TerminalSink(format="ascii", stream=buf)
        sink.write(_make_entry(
            level="ERROR",
            exception="division by zero",
            exception_type="ZeroDivisionError",
            return_value=None,
        ))
        out = buf.getvalue()
        assert "EXCEPTION ZeroDivisionError" in out

    def test_no_args(self):
        buf = io.StringIO()
        sink = TerminalSink(format="ascii", stream=buf, show_args=False)
        sink.write(_make_entry())
        out = buf.getvalue()
        assert "args=" not in out

    def test_no_return(self):
        buf = io.StringIO()
        sink = TerminalSink(format="ascii", stream=buf, show_return=False)
        sink.write(_make_entry())
        out = buf.getvalue()
        assert "-> 10" not in out

    def test_no_duration(self):
        buf = io.StringIO()
        sink = TerminalSink(format="ascii", stream=buf, show_duration=False)
        sink.write(_make_entry())
        out = buf.getvalue()
        assert "ms]" not in out


# ---------------------------------------------------------------------------
# Color format
# ---------------------------------------------------------------------------

class TestColorFormat:

    def test_basic_output(self):
        buf = io.StringIO()
        sink = TerminalSink(format="color", stream=buf)
        sink.write(_make_entry())
        out = buf.getvalue()
        assert "add" in out
        assert "\033[" in out  # ANSI escape present

    def test_slow_duration_highlighted(self):
        buf = io.StringIO()
        sink = TerminalSink(format="color", stream=buf)
        sink.write(_make_entry(duration_ms=2500))
        out = buf.getvalue()
        assert "2.5s" in out

    def test_medium_duration(self):
        buf = io.StringIO()
        sink = TerminalSink(format="color", stream=buf)
        sink.write(_make_entry(duration_ms=250))
        out = buf.getvalue()
        assert "250ms" in out

    def test_traceback_shown(self):
        buf = io.StringIO()
        sink = TerminalSink(format="color", stream=buf, show_traceback=True)
        sink.write(_make_entry(
            level="ERROR",
            exception="oops",
            exception_type="RuntimeError",
            traceback="Traceback:\n  File x.py\n    ...\nRuntimeError: oops",
            return_value=None,
        ))
        out = buf.getvalue()
        assert "RuntimeError: oops" in out

    def test_exception_color(self):
        buf = io.StringIO()
        sink = TerminalSink(format="color", stream=buf)
        sink.write(_make_entry(
            level="ERROR",
            exception="fail",
            exception_type="ValueError",
            return_value=None,
        ))
        out = buf.getvalue()
        assert "ValueError" in out


# ---------------------------------------------------------------------------
# Markdown format
# ---------------------------------------------------------------------------

class TestMarkdownFormat:

    def test_basic_output(self):
        buf = io.StringIO()
        sink = TerminalSink(format="markdown", stream=buf)
        sink.write(_make_entry())
        out = buf.getvalue()
        assert "add()" in out
        assert "OK" in out

    def test_error_output(self):
        buf = io.StringIO()
        sink = TerminalSink(format="markdown", stream=buf)
        sink.write(_make_entry(
            level="ERROR",
            exception="fail",
            exception_type="ValueError",
            return_value=None,
        ))
        out = buf.getvalue()
        assert "ERROR" in out
        assert "ValueError" in out

    def test_shows_kwargs(self):
        buf = io.StringIO()
        sink = TerminalSink(format="markdown", stream=buf)
        sink.write(_make_entry(kwargs={"force": True}))
        out = buf.getvalue()
        assert "kwargs" in out or "force" in out

    def test_duration_shown(self):
        buf = io.StringIO()
        sink = TerminalSink(format="markdown", stream=buf)
        sink.write(_make_entry(duration_ms=42.7))
        out = buf.getvalue()
        assert "42.7ms" in out

    def test_meta_shown(self):
        buf = io.StringIO()
        sink = TerminalSink(format="markdown", stream=buf)
        sink.write(_make_entry(extra={"args_meta": [{"type": "image"}]}))
        out = buf.getvalue()
        assert "meta" in out


# ---------------------------------------------------------------------------
# TOON format
# ---------------------------------------------------------------------------

class TestToonFormat:

    def test_basic_output(self):
        buf = io.StringIO()
        sink = TerminalSink(format="toon", stream=buf)
        sink.write(_make_entry())
        out = buf.getvalue()
        assert "09:30:23" in out
        assert "DEBUG" in out
        assert "add(" in out
        assert "->10" in out
        assert "[1.5ms]" in out

    def test_exception_output(self):
        buf = io.StringIO()
        sink = TerminalSink(format="toon", stream=buf)
        sink.write(_make_entry(
            level="ERROR",
            exception="division by zero",
            exception_type="ZeroDivisionError",
            return_value=None,
        ))
        out = buf.getvalue()
        assert "!ZeroDivisionError" in out

    def test_slow_duration(self):
        buf = io.StringIO()
        sink = TerminalSink(format="toon", stream=buf)
        sink.write(_make_entry(duration_ms=5000))
        out = buf.getvalue()
        assert "[5.0s]" in out

    def test_kwargs_shown(self):
        buf = io.StringIO()
        sink = TerminalSink(format="toon", stream=buf)
        sink.write(_make_entry(args=(), kwargs={"force": True}))
        out = buf.getvalue()
        assert "force=" in out

    def test_binary_meta(self):
        buf = io.StringIO()
        sink = TerminalSink(format="toon", stream=buf)
        entry = _make_entry(extra={
            "meta_log": True,
            "args_meta": [
                {"img": {"format": "PNG", "width": 1920, "height": 1080, "size_bytes": 5242880}}
            ],
        })
        sink.write(entry)
        out = buf.getvalue()
        assert "meta:" in out
        assert "PNG" in out


# ---------------------------------------------------------------------------
# Table format
# ---------------------------------------------------------------------------

class TestTableFormat:

    def test_basic_output(self):
        buf = io.StringIO()
        sink = TerminalSink(format="table", stream=buf)
        sink.write(_make_entry())
        out = buf.getvalue()
        # Should contain function name and time regardless of rich availability
        assert "add" in out

    def test_exception_in_table(self):
        buf = io.StringIO()
        sink = TerminalSink(format="table", stream=buf)
        sink.write(_make_entry(
            level="ERROR",
            exception="fail",
            exception_type="TypeError",
            return_value=None,
        ))
        out = buf.getvalue()
        assert "TypeError" in out


# ---------------------------------------------------------------------------
# Sink properties and delegation
# ---------------------------------------------------------------------------

class TestSinkProperties:

    def test_format_property(self):
        sink = TerminalSink(format="toon")
        assert sink.format == "toon"

    def test_unknown_format_falls_back_to_ascii(self):
        buf = io.StringIO()
        sink = TerminalSink(format="nonexistent", stream=buf)
        sink.write(_make_entry())
        out = buf.getvalue()
        assert "add()" in out  # ascii fallback

    def test_delegate_receives_entry(self):
        buf = io.StringIO()
        delegate_buf = io.StringIO()
        delegate = TerminalSink(format="ascii", stream=delegate_buf)
        sink = TerminalSink(format="toon", stream=buf, delegate=delegate)
        sink.write(_make_entry())
        assert "add" in buf.getvalue()
        assert "add()" in delegate_buf.getvalue()

    def test_close_closes_delegate(self):
        closed = []

        class MockSink:
            def write(self, entry):
                pass
            def close(self):
                closed.append(True)

        sink = TerminalSink(delegate=MockSink())
        sink.close()
        assert closed == [True]

    def test_close_without_delegate(self):
        sink = TerminalSink()
        sink.close()  # should not raise

    def test_none_duration(self):
        buf = io.StringIO()
        sink = TerminalSink(format="ascii", stream=buf)
        sink.write(_make_entry(duration_ms=None))
        out = buf.getvalue()
        assert "ms]" not in out

    def test_none_return_value(self):
        buf = io.StringIO()
        sink = TerminalSink(format="ascii", stream=buf)
        sink.write(_make_entry(return_value=None))
        out = buf.getvalue()
        assert "->" not in out
