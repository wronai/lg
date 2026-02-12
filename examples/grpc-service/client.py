#!/usr/bin/env python3
"""
nfo example — gRPC Python client.

Demonstrates all four RPCs: LogCall, BatchLog, StreamLog, QueryLogs.

Requirements:
    pip install grpcio

Generate stubs (if not already present):
    cd examples/
    python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. nfo.proto

Start server first:
    python examples/grpc_server.py

Then run this client:
    python examples/grpc_client.py
    python examples/grpc_client.py --host localhost:50051
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

try:
    import grpc
except ImportError:
    raise SystemExit(
        "This example requires grpcio:\n"
        "  pip install grpcio\n"
    )

# Ensure grpc-service/ is on sys.path for generated stubs
sys.path.insert(0, str(Path(__file__).parent))

import nfo_pb2
import nfo_pb2_grpc


def run_demo(target: str = "localhost:50051"):
    """Run all four gRPC RPCs against nfo server."""

    print(f"=== nfo gRPC Client Demo ===")
    print(f"Server: {target}\n")

    channel = grpc.insecure_channel(target)
    stub = nfo_pb2_grpc.NfoLoggerStub(channel)

    # --- 1. LogCall (single entry) ---
    print("--- 1. LogCall (single entry) ---")
    resp = stub.LogCall(nfo_pb2.LogRequest(
        cmd="deploy",
        args=["prod", "v2.1.0"],
        language="bash",
        env="prod",
        success=True,
        duration_ms=1234.5,
        output="Deployment successful",
    ))
    print(f"  stored={resp.stored}  id={resp.id}  ts={resp.timestamp}")

    # --- 2. BatchLog (multiple entries) ---
    print("\n--- 2. BatchLog (3 entries) ---")
    batch_resp = stub.BatchLog(nfo_pb2.BatchLogRequest(
        entries=[
            nfo_pb2.LogRequest(
                cmd="build",
                args=["--release"],
                language="rust",
                env="ci",
                success=True,
                duration_ms=45678.0,
            ),
            nfo_pb2.LogRequest(
                cmd="test",
                args=["--all", "--parallel"],
                language="go",
                env="ci",
                success=True,
                duration_ms=12000.0,
            ),
            nfo_pb2.LogRequest(
                cmd="lint",
                args=["src/"],
                language="python",
                env="ci",
                success=False,
                error="E501: line too long (120 > 88)",
                duration_ms=890.0,
            ),
        ]
    ))
    print(f"  stored={batch_resp.stored} entries")
    for r in batch_resp.results:
        print(f"    id={r.id}  ts={r.timestamp}")

    # --- 3. StreamLog (bidirectional streaming) ---
    print("\n--- 3. StreamLog (5 entries, bidirectional) ---")

    def generate_requests():
        commands = [
            ("migrate", ["--target", "v3"], "python"),
            ("backup", ["daily", "s3://bucket"], "bash"),
            ("healthcheck", ["api", "db", "cache"], "bash"),
            ("restart", ["worker-1", "worker-2"], "bash"),
            ("notify", ["slack", "#deploys"], "python"),
        ]
        for cmd, args, lang in commands:
            yield nfo_pb2.LogRequest(
                cmd=cmd,
                args=args,
                language=lang,
                env="prod",
                success=True,
                duration_ms=float(hash(cmd) % 5000),
            )

    responses = stub.StreamLog(generate_requests())
    for resp in responses:
        print(f"  stored={resp.stored}  id={resp.id}  ts={resp.timestamp}")

    # --- 4. QueryLogs ---
    print("\n--- 4. QueryLogs (all entries) ---")
    query_resp = stub.QueryLogs(nfo_pb2.QueryRequest(
        limit=20,
    ))
    print(f"  total in DB: {query_resp.total}")
    print(f"  returned: {len(query_resp.entries)}")
    for e in query_resp.entries:
        err_str = f" | ERROR: {e.error[:40]}" if e.error else ""
        print(f"    {e.timestamp[:19]} | {e.level:5s} | {e.cmd} [{e.language}] | {e.duration_ms:.0f}ms{err_str}")

    # --- 5. QueryLogs with filters ---
    print("\n--- 5. QueryLogs (errors only) ---")
    err_resp = stub.QueryLogs(nfo_pb2.QueryRequest(
        level="ERROR",
        limit=10,
    ))
    print(f"  errors found: {len(err_resp.entries)}")
    for e in err_resp.entries:
        print(f"    {e.cmd} [{e.language}] — {e.error[:60]}")

    channel.close()
    print("\nDone. All RPCs completed successfully.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="nfo gRPC Client Demo")
    parser.add_argument(
        "--host", default=os.environ.get("NFO_GRPC_HOST", "localhost:50051"),
        help="gRPC server address (default: localhost:50051)"
    )
    args = parser.parse_args()
    run_demo(args.host)
