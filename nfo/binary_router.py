"""Sink that routes log entries based on binary data presence.

- Entries with ``extra["meta_log"] == True`` → *lightweight_sink*
- Entries with large raw data in args   → *heavy_sink* (optional)
- Everything else                       → *full_sink*
"""

from __future__ import annotations

from typing import Optional

from nfo.models import LogEntry
from nfo.sinks import Sink


class BinaryAwareRouter(Sink):
    """Route log entries to different sinks based on payload characteristics.

    Args:
        lightweight_sink: Target for meta-log entries (fast, e.g. JSON).
        full_sink: Target for regular log entries (e.g. SQLite).
        heavy_sink: Optional target for entries with large raw data.
        size_threshold: Byte threshold for detecting large raw data in args.
    """

    def __init__(
        self,
        lightweight_sink: Sink,
        full_sink: Sink,
        heavy_sink: Optional[Sink] = None,
        size_threshold: int = 65536,
    ) -> None:
        self._light = lightweight_sink
        self._full = full_sink
        self._heavy = heavy_sink
        self._threshold = size_threshold

    def write(self, entry: LogEntry) -> None:
        if entry.extra.get("meta_log"):
            self._light.write(entry)
        elif self._heavy and self._has_large_data(entry):
            self._heavy.write(entry)
        else:
            self._full.write(entry)

    def _has_large_data(self, entry: LogEntry) -> bool:
        for arg in entry.args:
            if isinstance(arg, (bytes, bytearray)) and len(arg) > self._threshold:
                return True
        if entry.return_value is not None and isinstance(
            entry.return_value, (bytes, bytearray)
        ):
            if len(entry.return_value) > self._threshold:
                return True
        return False

    def close(self) -> None:
        self._light.close()
        self._full.close()
        if self._heavy:
            self._heavy.close()
