"""
lg — Automatic function logging with decorators.

Output to SQLite, CSV, and Markdown.
"""

from lg.decorators import log_call, catch
from lg.logger import Logger
from lg.sinks import SQLiteSink, CSVSink, MarkdownSink

__version__ = "0.1.0"

__all__ = [
    "log_call",
    "catch",
    "Logger",
    "SQLiteSink",
    "CSVSink",
    "MarkdownSink",
]
