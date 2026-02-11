"""Sinks for writing log entries to various backends (SQLite, CSV, Markdown)."""

from __future__ import annotations

import csv
import io
import os
import sqlite3
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

from nfo.models import LogEntry

_COLUMNS = [
    "timestamp",
    "level",
    "function_name",
    "module",
    "args",
    "kwargs",
    "arg_types",
    "kwarg_types",
    "return_value",
    "return_type",
    "exception",
    "exception_type",
    "traceback",
    "duration_ms",
    "environment",
    "trace_id",
    "version",
    "llm_analysis",
]


class Sink(ABC):
    """Base class for all sinks."""

    @abstractmethod
    def write(self, entry: LogEntry) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...


# ---------------------------------------------------------------------------
# SQLite
# ---------------------------------------------------------------------------

class SQLiteSink(Sink):
    """Persist log entries to a SQLite database."""

    def __init__(self, db_path: str | Path = "logs.db", table: str = "logs") -> None:
        self.db_path = str(db_path)
        self.table = table
        self._lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None
        self._ensure_table()

    # -- internal helpers ----------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        return self._conn

    def _ensure_table(self) -> None:
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {self.table} ("
                "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "  timestamp TEXT,"
                "  level TEXT,"
                "  function_name TEXT,"
                "  module TEXT,"
                "  args TEXT,"
                "  kwargs TEXT,"
                "  arg_types TEXT,"
                "  kwarg_types TEXT,"
                "  return_value TEXT,"
                "  return_type TEXT,"
                "  exception TEXT,"
                "  exception_type TEXT,"
                "  traceback TEXT,"
                "  duration_ms REAL,"
                "  environment TEXT,"
                "  trace_id TEXT,"
                "  version TEXT,"
                "  llm_analysis TEXT"
                ")"
            )
            conn.commit()

    # -- public API ----------------------------------------------------------

    def write(self, entry: LogEntry) -> None:
        row = entry.as_dict()
        cols = ", ".join(_COLUMNS)
        placeholders = ", ".join(["?"] * len(_COLUMNS))
        values = [row[c] for c in _COLUMNS]
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                f"INSERT INTO {self.table} ({cols}) VALUES ({placeholders})",
                values,
            )
            conn.commit()

    def close(self) -> None:
        with self._lock:
            if self._conn:
                self._conn.close()
                self._conn = None


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

class CSVSink(Sink):
    """Append log entries to a CSV file."""

    def __init__(self, file_path: str | Path = "logs.csv") -> None:
        self.file_path = str(file_path)
        self._lock = threading.Lock()
        self._write_header_if_needed()

    def _write_header_if_needed(self) -> None:
        if not os.path.exists(self.file_path) or os.path.getsize(self.file_path) == 0:
            with open(self.file_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(_COLUMNS)

    def write(self, entry: LogEntry) -> None:
        row = entry.as_dict()
        with self._lock:
            with open(self.file_path, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([row[c] for c in _COLUMNS])

    def close(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

class MarkdownSink(Sink):
    """Append log entries to a Markdown file as structured sections."""

    def __init__(self, file_path: str | Path = "logs.md") -> None:
        self.file_path = str(file_path)
        self._lock = threading.Lock()
        self._write_header_if_needed()

    def _write_header_if_needed(self) -> None:
        if not os.path.exists(self.file_path) or os.path.getsize(self.file_path) == 0:
            with open(self.file_path, "w") as f:
                f.write("# Logs\n\n")

    def write(self, entry: LogEntry) -> None:
        d = entry.as_dict()
        lines = [
            f"## {d['timestamp']} | {d['level']} | `{d['function_name']}`\n",
            f"- **Module:** {d['module']}",
            f"- **Args:** `{d['args']}`",
            f"- **Kwargs:** `{d['kwargs']}`",
            f"- **Arg types:** {d['arg_types']}",
            f"- **Duration:** {d['duration_ms']} ms",
        ]
        if d["return_type"]:
            lines.append(f"- **Return:** `{d['return_value']}` ({d['return_type']})")
        if d["exception"]:
            lines.append(f"- **Exception:** `{d['exception_type']}`: {d['exception']}")
            lines.append(f"\n```\n{d['traceback']}\n```")
        if d.get("environment"):
            lines.append(f"- **Environment:** {d['environment']}")
        if d.get("trace_id"):
            lines.append(f"- **Trace ID:** `{d['trace_id']}`")
        if d.get("version"):
            lines.append(f"- **Version:** {d['version']}")
        if d.get("llm_analysis"):
            lines.append(f"- **LLM Analysis:** {d['llm_analysis']}")
        lines.append("\n---\n")

        with self._lock:
            with open(self.file_path, "a") as f:
                f.write("\n".join(lines) + "\n")

    def close(self) -> None:
        pass
