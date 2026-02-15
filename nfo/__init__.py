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
from nfo.meta import ThresholdPolicy
from nfo.extractors import extract_meta, register_extractor
from nfo.meta_decorators import meta_log
from nfo.binary_router import BinaryAwareRouter
from nfo.buffered_sink import AsyncBufferedSink
from nfo.ring_buffer_sink import RingBufferSink
from nfo.terminal import TerminalSink

# Lazy import for optional click dependency
def _lazy_click():
    from nfo.click import NfoGroup, NfoCommand, nfo_options
    return NfoGroup, NfoCommand, nfo_options

# Lazy import for optional dependencies
def __getattr__(name: str):
    if name == "PrometheusSink":
        from nfo.prometheus import PrometheusSink
        return PrometheusSink
    if name in ("NfoGroup", "NfoCommand", "nfo_options"):
        from nfo import click as _click
        return getattr(_click, name)
    raise AttributeError(f"module 'nfo' has no attribute {name!r}")

__version__ = "0.3.0"

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
    "ThresholdPolicy",
    "extract_meta",
    "register_extractor",
    "meta_log",
    "BinaryAwareRouter",
    "AsyncBufferedSink",
    "RingBufferSink",
    "TerminalSink",
    "NfoGroup",
    "NfoCommand",
    "nfo_options",
]
