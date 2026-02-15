"""Asynchronous buffered sink — batches log entries and writes in a background thread.

For high-throughput pipelines where synchronous sink writes would block the
calling function.  Entries are collected in a thread-safe buffer and flushed
either when *buffer_size* is reached or every *flush_interval* seconds.
"""

from __future__ import annotations

import atexit
import collections
import threading
import time
from typing import Optional

from nfo.models import LogEntry
from nfo.sinks import Sink


class AsyncBufferedSink(Sink):
    """Buffer log entries and write them batch-wise in a background thread.

    Args:
        delegate: The downstream sink that receives flushed batches.
        buffer_size: Flush when this many entries are buffered.
        flush_interval: Flush at least every *N* seconds (even if buffer
            is not full).
        flush_on_error: If ``True``, flush immediately when an ERROR-level
            entry arrives (ensures errors are never delayed).
    """

    def __init__(
        self,
        delegate: Sink,
        buffer_size: int = 100,
        flush_interval: float = 1.0,
        flush_on_error: bool = True,
    ) -> None:
        self._delegate = delegate
        self._buffer_size = max(buffer_size, 1)
        self._flush_interval = flush_interval
        self._flush_on_error = flush_on_error

        self._buffer: collections.deque[LogEntry] = collections.deque()
        self._lock = threading.Lock()
        self._closed = False
        self._flush_event = threading.Event()

        self._thread = threading.Thread(
            target=self._flush_loop, daemon=True, name="nfo-buffered-sink"
        )
        self._thread.start()
        atexit.register(self.close)

    # -- public API ----------------------------------------------------------

    def write(self, entry: LogEntry) -> None:
        if self._closed:
            return
        with self._lock:
            self._buffer.append(entry)
            should_flush = (
                len(self._buffer) >= self._buffer_size
                or (self._flush_on_error and entry.level in ("ERROR", "CRITICAL"))
            )
        if should_flush:
            self._flush_event.set()

    def flush(self) -> None:
        """Force an immediate flush of the buffer (blocking)."""
        self._do_flush()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._flush_event.set()
        self._thread.join(timeout=5.0)
        self._do_flush()  # drain anything left
        self._delegate.close()

    @property
    def pending(self) -> int:
        """Number of entries waiting to be flushed."""
        return len(self._buffer)

    # -- internal ------------------------------------------------------------

    def _flush_loop(self) -> None:
        while not self._closed:
            self._flush_event.wait(timeout=self._flush_interval)
            self._flush_event.clear()
            self._do_flush()

    def _do_flush(self) -> None:
        with self._lock:
            if not self._buffer:
                return
            batch = list(self._buffer)
            self._buffer.clear()
        for entry in batch:
            try:
                self._delegate.write(entry)
            except Exception:
                pass  # logging path must not break the app
