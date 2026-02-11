"""Tests for nfo.sinks (SQLite, CSV, Markdown)."""

import csv
import os
import sqlite3
import tempfile

import pytest

from nfo.models import LogEntry
from nfo.sinks import SQLiteSink, CSVSink, MarkdownSink


def _make_entry(**overrides) -> LogEntry:
    defaults = dict(
        timestamp=LogEntry.now(),
        level="DEBUG",
        function_name="my_func",
        module="test_sinks",
        args=(1, "a"),
        kwargs={"key": "val"},
        arg_types=["int", "str"],
        kwarg_types={"key": "str"},
        return_value=42,
        return_type="int",
        duration_ms=1.234,
    )
    defaults.update(overrides)
    return LogEntry(**defaults)


# -- SQLite -------------------------------------------------------------------

class TestSQLiteSink:

    def test_write_and_query(self, tmp_path):
        db = tmp_path / "test.db"
        sink = SQLiteSink(db_path=db)
        sink.write(_make_entry())
        sink.write(_make_entry(level="ERROR", exception="fail", exception_type="ValueError"))

        conn = sqlite3.connect(str(db))
        rows = conn.execute("SELECT * FROM logs").fetchall()
        conn.close()
        sink.close()

        assert len(rows) == 2

    def test_custom_table(self, tmp_path):
        db = tmp_path / "test.db"
        sink = SQLiteSink(db_path=db, table="app_logs")
        sink.write(_make_entry())

        conn = sqlite3.connect(str(db))
        rows = conn.execute("SELECT * FROM app_logs").fetchall()
        conn.close()
        sink.close()

        assert len(rows) == 1


# -- CSV ----------------------------------------------------------------------

class TestCSVSink:

    def test_write_rows(self, tmp_path):
        fp = tmp_path / "test.csv"
        sink = CSVSink(file_path=fp)
        sink.write(_make_entry())
        sink.write(_make_entry())
        sink.close()

        with open(fp) as f:
            reader = list(csv.reader(f))

        assert reader[0][0] == "timestamp"  # header
        assert len(reader) == 3  # header + 2 rows

    def test_does_not_duplicate_header(self, tmp_path):
        fp = tmp_path / "test.csv"
        sink1 = CSVSink(file_path=fp)
        sink1.write(_make_entry())
        sink1.close()

        sink2 = CSVSink(file_path=fp)
        sink2.write(_make_entry())
        sink2.close()

        with open(fp) as f:
            lines = f.readlines()

        header_count = sum(1 for l in lines if l.startswith("timestamp"))
        assert header_count == 1


# -- Markdown -----------------------------------------------------------------

class TestMarkdownSink:

    def test_write_entry(self, tmp_path):
        fp = tmp_path / "test.md"
        sink = MarkdownSink(file_path=fp)
        sink.write(_make_entry())
        sink.close()

        content = fp.read_text()
        assert "# Logs" in content
        assert "## " in content
        assert "`my_func`" in content

    def test_exception_block(self, tmp_path):
        fp = tmp_path / "test.md"
        sink = MarkdownSink(file_path=fp)
        sink.write(_make_entry(
            exception="bad input",
            exception_type="ValueError",
            traceback="Traceback ...\nValueError: bad input",
        ))
        sink.close()

        content = fp.read_text()
        assert "ValueError" in content
        assert "```" in content
