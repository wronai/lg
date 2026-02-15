"""Threshold policy for deciding when to log full data vs metadata."""

from __future__ import annotations

import dataclasses
import sys
from typing import Any, Optional


@dataclasses.dataclass
class ThresholdPolicy:
    """Policy deciding when to log full data vs extracted metadata.

    When a value exceeds the configured byte thresholds, the logging
    system extracts lightweight metadata (format, size, hash) instead
    of calling ``repr()`` on potentially huge payloads.
    """

    max_arg_bytes: int = 8192        # 8 KB — above this: metadata only
    max_return_bytes: int = 8192     # 8 KB for return values
    max_total_bytes: int = 65536     # 64 KB total limit per entry
    binary_threshold: float = 0.3    # fraction of non-printable chars → treat as binary

    def should_extract_meta(self, value: Any) -> bool:
        """Return True if *value* should be represented as metadata."""
        if isinstance(value, (bytes, bytearray, memoryview)):
            size = len(value) if not isinstance(value, memoryview) else value.nbytes
            return size > self.max_arg_bytes
        if isinstance(value, str):
            return len(value.encode("utf-8", errors="ignore")) > self.max_arg_bytes
        # numpy-like (duck-typed)
        if hasattr(value, "__len__") and hasattr(value, "dtype"):
            try:
                return value.nbytes > self.max_arg_bytes
            except Exception:
                return False
        # file-like objects — always extract meta
        if hasattr(value, "read") and hasattr(value, "tell"):
            return True
        return False

    def should_extract_return_meta(self, value: Any) -> bool:
        """Like :meth:`should_extract_meta` but uses ``max_return_bytes``."""
        saved = self.max_arg_bytes
        try:
            self.max_arg_bytes = self.max_return_bytes
            return self.should_extract_meta(value)
        finally:
            self.max_arg_bytes = saved


def sizeof(obj: Any) -> int:
    """Best-effort size of *obj* in bytes."""
    try:
        if isinstance(obj, (bytes, bytearray)):
            return len(obj)
        if isinstance(obj, memoryview):
            return obj.nbytes
        if hasattr(obj, "nbytes"):
            return obj.nbytes
        return sys.getsizeof(obj)
    except Exception:
        return -1
