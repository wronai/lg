"""Ring-buffer sink — keeps last N entries in memory, flushes on ERROR.

Zero-overhead diagnostics: no disk writes during normal operation.  When an
ERROR (or CRITICAL) entry arrives, the entire ring buffer (preceding context)
plus the error entry are flushed to the delegate sink.  This gives you the
"why did this error happen" context without continuous I/O.
"""

from __future__ import annotations

import collections
import threading
from typing import Optional, Sequence

from nfo.models import LogEntry
from nfo.sinks import Sink


class RingBufferSink(Sink):
    """In-memory ring buffer that flushes context to *delegate* on error.

    Args:
        delegate: Downstream sink that receives flushed entries.
        capacity: Maximum number of entries kept in the ring buffer.
        trigger_levels: Log levels that trigger a flush (default: ERROR, CRITICAL).
        include_trigger: If ``True`` (default), the triggering entry is also
            written to the delegate.
    """

    def __init__(
        self,
        delegate: Sink,
        capacity: int = 1000,
        trigger_levels: Optional[Sequence[str]] = None,
        include_trigger: bool = True,
    ) -> None:
        self._delegate = delegate
        self._buffer: collections.deque[LogEntry] = collections.deque(maxlen=max(capacity, 1))
        self._trigger_levels = frozenset(
            level.upper() for level in (trigger_levels or ("ERROR", "CRITICAL"))
        )
        self._include_trigger = include_trigger
        self._lock = threading.Lock()
        self._flush_count = 0

    # -- public API ----------------------------------------------------------

    def write(self, entry: LogEntry) -> None:
        with self._lock:
            if entry.level.upper() in self._trigger_levels:
                # Flush buffered context + trigger entry
                for buffered in self._buffer:
                    try:
                        self._delegate.write(buffered)
                    except Exception:
                        pass
                if self._include_trigger:
                    try:
                        self._delegate.write(entry)
                    except Exception:
                        pass
                self._buffer.clear()
                self._flush_count += 1
            else:
                self._buffer.append(entry)

    def close(self) -> None:
        with self._lock:
            self._buffer.clear()
        self._delegate.close()

    @property
    def buffered(self) -> int:
        """Number of entries currently in the ring buffer."""
        return len(self._buffer)

    @property
    def flush_count(self) -> int:
        """Number of times the buffer has been flushed (error events seen)."""
        return self._flush_count

    @property
    def capacity(self) -> int:
        """Maximum ring buffer size."""
        return self._buffer.maxlen or 0
