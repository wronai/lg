"""
nfo — Automatic function logging with decorators.

Output to SQLite, CSV, and Markdown.
"""

from nfo.decorators import log_call, catch
from nfo.logger import Logger
from nfo.sinks import SQLiteSink, CSVSink, MarkdownSink
from nfo.configure import configure
from nfo.logged import logged, skip
from nfo.env import EnvTagger, DynamicRouter, DiffTracker
from nfo.llm import LLMSink, detect_prompt_injection, scan_entry_for_injection
from nfo.auto import auto_log, auto_log_by_name

__version__ = "0.1.9"

__all__ = [
    "log_call",
    "catch",
    "logged",
    "skip",
    "configure",
    "Logger",
    "SQLiteSink",
    "CSVSink",
    "MarkdownSink",
    "LLMSink",
    "EnvTagger",
    "DynamicRouter",
    "DiffTracker",
    "detect_prompt_injection",
    "scan_entry_for_injection",
    "auto_log",
    "auto_log_by_name",
]
