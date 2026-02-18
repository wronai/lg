"""
nfo.fastapi_middleware — Starlette/FastAPI middleware for structured request logging.

Logs every HTTP request as a nfo LogEntry with:
  - method, path, status_code, duration_ms
  - client IP, query string
  - structured kwargs → goes to SQLite/CSV/Markdown sinks automatically

Usage::

    from fastapi import FastAPI
    import nfo

    nfo.configure(sinks=["sqlite:requests.db"])

    app = FastAPI()
    app.add_middleware(nfo.FastAPIMiddleware)

    # or with options:
    app.add_middleware(
        nfo.FastAPIMiddleware,
        skip_paths=["/api/status", "/docs", "/openapi.json"],
        log_level="INFO",
    )
"""

from __future__ import annotations

import time
import logging
from typing import Sequence

log = logging.getLogger("nfo.fastapi")


class FastAPIMiddleware:
    """
    ASGI middleware that emits one nfo LogEntry per HTTP request.

    Each entry has:
      - ``function_name``: ``"http.{method}.{path}"`` e.g. ``"http.GET./api/status"``
      - ``return_value``: HTTP status code as string
      - ``duration_ms``: wall-clock time for the full request
      - ``extra``: dict with method, path, status, client, query, duration_ms

    Compatible with FastAPI, Starlette, and any ASGI framework.
    """

    def __init__(
        self,
        app,
        skip_paths: Sequence[str] = ("/docs", "/openapi.json", "/redoc"),
        log_level: str = "INFO",
        skip_2xx: bool = False,
    ) -> None:
        self.app = app
        self.skip_paths = set(skip_paths)
        self.log_level = log_level.upper()
        self.skip_2xx = skip_2xx

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        method = scope.get("method", "GET")
        query = scope.get("query_string", b"").decode("utf-8", errors="replace")
        client = scope.get("client")
        client_ip = client[0] if client else "unknown"

        if path in self.skip_paths:
            await self.app(scope, receive, send)
            return

        status_code = 0
        started_at = time.time()

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            self._emit(method, path, 500, time.time() - started_at,
                       client_ip, query, error=str(exc))
            raise

        duration_ms = (time.time() - started_at) * 1000

        if self.skip_2xx and 200 <= status_code < 300:
            return

        self._emit(method, path, status_code, duration_ms, client_ip, query)

    def _emit(
        self,
        method: str,
        path: str,
        status: int,
        duration_ms: float,
        client: str,
        query: str,
        error: str | None = None,
    ) -> None:
        from nfo.configure import _last_logger
        from nfo.models import LogEntry

        level = "ERROR" if status >= 500 else "WARNING" if status >= 400 else self.log_level
        func_name = f"http.{method}.{path}"

        extra = {
            "method": method,
            "path": path,
            "status": status,
            "client": client,
            "duration_ms": round(duration_ms, 1),
        }
        if query:
            extra["query"] = query
        if error:
            extra["error"] = error

        if _last_logger is not None:
            entry = LogEntry(
                timestamp=LogEntry.now(),
                level=level,
                function_name=func_name,
                module="nfo.fastapi",
                args=(),
                kwargs=extra,
                arg_types=[],
                kwarg_types={},
                return_value=str(status),
                return_type="int",
                exception=error,
                exception_type="HTTPError" if error else None,
                traceback=None,
                duration_ms=round(duration_ms, 1),
                extra=extra,
            )
            _last_logger.emit(entry)
        else:
            log.log(
                getattr(logging, level, logging.INFO),
                "%s %s → %d (%.0fms)",
                method, path, status, duration_ms,
            )
