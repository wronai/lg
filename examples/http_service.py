#!/usr/bin/env python3
"""
nfo example — centralized HTTP logging service.

Standalone FastAPI service that accepts log entries from any language/technology
via HTTP POST. All logs are stored in a single SQLite database.

Requirements:
    pip install nfo fastapi uvicorn

Start:
    uvicorn examples.http_service:app --port 8080
    # or: python examples/http_service.py

Send logs from any language:
    curl -X POST http://localhost:8080/log \\
        -H "Content-Type: application/json" \\
        -d '{"cmd":"deploy","args":["prod"],"language":"bash"}'

    curl http://localhost:8080/logs
    curl http://localhost:8080/logs?language=bash&success=false
"""

from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path
from typing import List, Optional

from nfo import Logger, SQLiteSink, CSVSink, JSONSink

# ---------------------------------------------------------------------------
# Try to import FastAPI; provide helpful error if missing
# ---------------------------------------------------------------------------
try:
    from fastapi import FastAPI, Query
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
except ImportError:
    raise SystemExit(
        "This example requires FastAPI and uvicorn:\n"
        "  pip install fastapi uvicorn\n"
    )

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LOG_DIR = os.environ.get("NFO_LOG_DIR", str(Path(__file__).parent))
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

DB_PATH = f"{LOG_DIR}/nfo_central.db"
CSV_PATH = f"{LOG_DIR}/nfo_central.csv"
JSONL_PATH = f"{LOG_DIR}/nfo_central.jsonl"

# ---------------------------------------------------------------------------
# nfo Logger setup
# ---------------------------------------------------------------------------

logger = Logger(
    name="nfo-service",
    sinks=[
        SQLiteSink(db_path=DB_PATH),
        CSVSink(file_path=CSV_PATH),
        JSONSink(file_path=JSONL_PATH),
    ],
    propagate_stdlib=True,
)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class LogEntry(BaseModel):
    cmd: str
    args: list = []
    language: str = "bash"
    env: str = "prod"
    success: Optional[bool] = None
    duration_ms: Optional[float] = None
    output: Optional[str] = None
    error: Optional[str] = None


class LogBatchRequest(BaseModel):
    entries: List[LogEntry]


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="nfo Centralized Logging Service",
    description="Accept log entries from any language via HTTP POST",
    version="0.2.0",
)


def _store_entry(entry: LogEntry) -> dict:
    """Write a single log entry through nfo and return result."""
    from nfo.models import LogEntry as NfoEntry

    nfo_entry = NfoEntry(
        function_name=entry.cmd,
        args=tuple(entry.args),
        kwargs={
            "language": entry.language,
            "env": entry.env,
        },
        level="INFO" if entry.success is not False else "ERROR",
        return_value=entry.output,
        exception=entry.error,
        duration_ms=entry.duration_ms or 0.0,
    )
    logger.emit(nfo_entry)

    return {
        "cmd": entry.cmd,
        "language": entry.language,
        "stored": True,
    }


@app.post("/log")
async def log_call(entry: LogEntry):
    """Log a single call from any language."""
    result = _store_entry(entry)
    return result


@app.post("/log/batch")
async def log_batch(batch: LogBatchRequest):
    """Log multiple entries at once."""
    results = [_store_entry(e) for e in batch.entries]
    return {"stored": len(results), "results": results}


@app.get("/logs")
async def get_logs(
    language: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
):
    """Query stored logs from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    query = "SELECT * FROM logs WHERE 1=1"
    params: list = []

    if level:
        query += " AND level = ?"
        params.append(level.upper())

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/health")
async def health():
    return {"status": "ok", "db": DB_PATH}


# ---------------------------------------------------------------------------
# Run with: python examples/http_service.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    print(f"nfo Centralized Logging Service")
    print(f"  DB:   {DB_PATH}")
    print(f"  CSV:  {CSV_PATH}")
    print(f"  JSONL: {JSONL_PATH}")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8080)
