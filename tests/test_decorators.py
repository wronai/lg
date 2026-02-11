"""Tests for nfo.decorators."""

import pytest

from nfo import log_call, catch, Logger
from nfo.decorators import set_default_logger
from nfo.models import LogEntry
from nfo.sinks import Sink


class MemorySink(Sink):
    """In-memory sink that collects entries for assertions."""

    def __init__(self):
        self.entries: list[LogEntry] = []

    def write(self, entry: LogEntry) -> None:
        self.entries.append(entry)

    def close(self) -> None:
        self.entries.clear()


@pytest.fixture()
def logger():
    sink = MemorySink()
    lgr = Logger(name="test", propagate_stdlib=False, sinks=[sink])
    set_default_logger(lgr)
    yield lgr, sink
    lgr.close()


# -- @log_call ---------------------------------------------------------------

class TestLogCall:

    def test_logs_args_and_return(self, logger):
        lgr, sink = logger

        @log_call
        def add(a, b):
            return a + b

        result = add(1, 2)
        assert result == 3
        assert len(sink.entries) == 1
        entry = sink.entries[0]
        assert entry.function_name == "TestLogCall.test_logs_args_and_return.<locals>.add"
        assert entry.args == (1, 2)
        assert entry.return_value == 3
        assert entry.return_type == "int"
        assert entry.level == "DEBUG"
        assert entry.duration_ms is not None

    def test_logs_kwargs(self, logger):
        lgr, sink = logger

        @log_call
        def greet(name="world"):
            return f"hello {name}"

        greet(name="nfo")
        entry = sink.entries[0]
        assert entry.kwargs == {"name": "nfo"}
        assert entry.kwarg_types == {"name": "str"}

    def test_logs_exception(self, logger):
        lgr, sink = logger

        @log_call
        def fail():
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            fail()

        assert len(sink.entries) == 1
        entry = sink.entries[0]
        assert entry.level == "ERROR"
        assert entry.exception == "boom"
        assert entry.exception_type == "ValueError"
        assert entry.traceback is not None

    def test_custom_level(self, logger):
        lgr, sink = logger

        @log_call(level="INFO")
        def noop():
            pass

        noop()
        assert sink.entries[0].level == "INFO"

    def test_arg_types(self, logger):
        lgr, sink = logger

        @log_call
        def mixed(a: int, b: str, c: list):
            pass

        mixed(1, "x", [1, 2])
        entry = sink.entries[0]
        assert entry.arg_types == ["int", "str", "list"]


# -- @catch -------------------------------------------------------------------

class TestCatch:

    def test_suppresses_exception(self, logger):
        lgr, sink = logger

        @catch
        def fail():
            raise RuntimeError("oops")

        result = fail()
        assert result is None
        assert len(sink.entries) == 1
        assert sink.entries[0].level == "ERROR"

    def test_returns_default(self, logger):
        lgr, sink = logger

        @catch(default=-1)
        def fail():
            raise RuntimeError("oops")

        assert fail() == -1

    def test_success_path(self, logger):
        lgr, sink = logger

        @catch
        def ok():
            return 42

        assert ok() == 42
        assert sink.entries[0].return_value == 42
