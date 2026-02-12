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
from nfo.json_sink import JSONSink
from nfo.webhook import WebhookSink

# Lazy import for optional prometheus dependency
def __getattr__(name: str):
    if name == "PrometheusSink":
        from nfo.prometheus import PrometheusSink
        return PrometheusSink
    raise AttributeError(f"module 'nfo' has no attribute {name!r}")

__version__ = "0.2.1"

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
    "JSONSink",
    "LLMSink",
    "PrometheusSink",
    "WebhookSink",
    "EnvTagger",
    "DynamicRouter",
    "DiffTracker",
    "detect_prompt_injection",
    "scan_entry_for_injection",
    "auto_log",
    "auto_log_by_name",
]
