"""Data models for log entries."""

from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class LogEntry:
    """A single log entry produced by a decorated function call."""

    timestamp: datetime
    level: str
    function_name: str
    module: str
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    arg_types: List[str]
    kwarg_types: Dict[str, str]
    return_value: Any = None
    return_type: Optional[str] = None
    exception: Optional[str] = None
    exception_type: Optional[str] = None
    traceback: Optional[str] = None
    duration_ms: Optional[float] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def now() -> datetime:
        return datetime.now(timezone.utc)

    def as_dict(self) -> Dict[str, Any]:
        """Convert to a flat dictionary suitable for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "function_name": self.function_name,
            "module": self.module,
            "args": repr(self.args),
            "kwargs": repr(self.kwargs),
            "arg_types": ", ".join(self.arg_types),
            "kwarg_types": repr(self.kwarg_types),
            "return_value": repr(self.return_value),
            "return_type": self.return_type or "",
            "exception": self.exception or "",
            "exception_type": self.exception_type or "",
            "traceback": self.traceback or "",
            "duration_ms": self.duration_ms,
        }
