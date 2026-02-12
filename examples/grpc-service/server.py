#!/usr/bin/env python3
"""
nfo example — gRPC logging server.

High-performance gRPC alternative to the HTTP service. Implements all
four RPCs defined in nfo.proto: LogCall, BatchLog, StreamLog, QueryLogs.

Requirements:
    pip install nfo grpcio grpcio-tools

Generate stubs (if not already present):
    cd examples/
    python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. nfo.proto

Start:
    python examples/grpc_server.py
    # or: python examples/grpc_server.py --port 50051 --db logs/grpc.db

Test with client:
    python examples/grpc_client.py
"""

from __future__ import annotations

import os
import sqlite3
import sys
import time
from concurrent import futures
from pathlib import Path

try:
    import grpc
except ImportError:
    raise SystemExit(
        "This example requires grpcio:\n"
        "  pip install grpcio grpcio-tools\n"
    )

# Ensure grpc-service/ is on sys.path for generated stubs
sys.path.insert(0, str(Path(__file__).parent))

import nfo_pb2
import nfo_pb2_grpc

from nfo import Logger, SQLiteSink, CSVSink
from nfo.models import LogEntry as NfoEntry

# ---------------------------------------------------------------------------
# Configuration (from env / .env)
# ---------------------------------------------------------------------------

try:
    from dotenv import load_dotenv
    _examples_dir = Path(__file__).parent.parent
    _env = _examples_dir / ".env"
    if not _env.exists():
        _env = _examples_dir / ".env.example"
    if _env.exists():
        load_dotenv(_env, override=False)
except ImportError:
    pass

GRPC_PORT = int(os.environ.get("NFO_GRPC_PORT", "50051"))
LOG_DIR = os.environ.get("NFO_LOG_DIR", "./logs")
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
DB_PATH = os.environ.get("NFO_DB", f"{LOG_DIR}/nfo_grpc.db")

# ---------------------------------------------------------------------------
# nfo Logger
# ---------------------------------------------------------------------------

logger = Logger(
    name="nfo-grpc",
    sinks=[
        SQLiteSink(db_path=DB_PATH),
    ],
    propagate_stdlib=True,
)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

_entry_counter = 0


def _store_request(req: nfo_pb2.LogRequest) -> nfo_pb2.LogResponse:
    """Convert a gRPC LogRequest to nfo LogEntry, emit, return response."""
    global _entry_counter
    _entry_counter += 1

    entry = NfoEntry(
        timestamp=NfoEntry.now(),
        level="INFO" if not req.error else "ERROR",
        function_name=req.cmd,
        module=req.language or "unknown",
        args=tuple(req.args),
        kwargs={
            "language": req.language,
            "env": req.env,
            **(dict(req.extra) if req.extra else {}),
        },
        arg_types=[type(a).__name__ for a in req.args],
        kwarg_types={"language": "str", "env": "str"},
        return_value=req.output if req.output else None,
        return_type="str" if req.output else None,
        exception=req.error if req.error else None,
        exception_type="RemoteError" if req.error else None,
        duration_ms=req.duration_ms,
        environment=req.env or "unknown",
    )
    logger.emit(entry)

    return nfo_pb2.LogResponse(
        stored=True,
        id=str(_entry_counter),
        timestamp=entry.timestamp.isoformat(),
    )


# ---------------------------------------------------------------------------
# gRPC Servicer
# ---------------------------------------------------------------------------

class NfoLoggerServicer(nfo_pb2_grpc.NfoLoggerServicer):
    """Implementation of NfoLogger gRPC service."""

    def LogCall(self, request, context):
        """Log a single function call."""
        return _store_request(request)

    def BatchLog(self, request, context):
        """Log multiple entries in one round-trip."""
        results = [_store_request(e) for e in request.entries]
        return nfo_pb2.BatchLogResponse(
            stored=len(results),
            results=results,
        )

    def StreamLog(self, request_iterator, context):
        """Stream log entries (bidirectional)."""
        for request in request_iterator:
            yield _store_request(request)

    def QueryLogs(self, request, context):
        """Query stored logs from SQLite."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        query = "SELECT * FROM logs WHERE 1=1"
        params: list = []

        if request.language:
            query += " AND module = ?"
            params.append(request.language)

        if request.level:
            query += " AND level = ?"
            params.append(request.level.upper())

        if request.env:
            query += " AND environment = ?"
            params.append(request.env)

        if request.since:
            query += " AND timestamp >= ?"
            params.append(request.since)

        limit = request.limit if request.limit > 0 else 50
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()

        # Get total count
        count_q = "SELECT COUNT(*) FROM logs"
        total = conn.execute(count_q).fetchone()[0]
        conn.close()

        entries = []
        for row in rows:
            d = dict(row)
            entries.append(nfo_pb2.LogEntry(
                id=str(d.get("id", "")),
                timestamp=d.get("timestamp", ""),
                level=d.get("level", ""),
                cmd=d.get("function_name", ""),
                args=d.get("args", "").strip("()").replace("'", "").split(", ") if d.get("args") else [],
                language=d.get("module", ""),
                env=d.get("environment", ""),
                success=d.get("level") != "ERROR",
                duration_ms=d.get("duration_ms", 0.0) or 0.0,
                output=d.get("return_value", "") or "",
                error=d.get("exception", "") or "",
            ))

        return nfo_pb2.QueryResponse(
            entries=entries,
            total=total,
        )


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

def serve(port: int = GRPC_PORT, max_workers: int = 10):
    """Start the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    nfo_pb2_grpc.add_NfoLoggerServicer_to_server(NfoLoggerServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()

    print(f"nfo gRPC Logging Service")
    print(f"  Port: {port}")
    print(f"  DB:   {DB_PATH}")
    print(f"  RPCs: LogCall, BatchLog, StreamLog, QueryLogs")
    print(f"\nListening on [::]:{port} ...")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.stop(grace=2)
        logger.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="nfo gRPC Logging Service")
    parser.add_argument("--port", type=int, default=GRPC_PORT, help=f"gRPC port (default: {GRPC_PORT})")
    parser.add_argument("--db", default=DB_PATH, help=f"SQLite database path (default: {DB_PATH})")
    parser.add_argument("--workers", type=int, default=10, help="Max thread pool workers (default: 10)")
    args = parser.parse_args()

    # Override module-level DB_PATH if custom --db provided
    if args.db != DB_PATH:
        globals()["DB_PATH"] = args.db

    serve(port=args.port, max_workers=args.workers)
