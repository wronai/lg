"""
nfo — Automatic function logging with decorators.

Output to SQLite, CSV, and Markdown.
"""

from nfo.decorators import log_call, catch
from nfo.logger import Logger
from nfo.sinks import SQLiteSink, CSVSink, MarkdownSink

__version__ = "0.1.9"

__all__ = [
    "log_call",
    "catch",
    "Logger",
    "SQLiteSink",
    "CSVSink",
    "MarkdownSink",
]
