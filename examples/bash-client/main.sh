#!/bin/bash
# nfo example — Bash HTTP client for nfo centralized logging service.
#
# Zero-dependency Bash client that sends log entries to nfo-service via curl.
# Pair with examples/http_service.py.
#
# Usage:
#   source examples/bash_client.sh
#   nfo_log "deploy" prod
#   nfo_run ./deploy.sh prod
#
# Environment:
#   NFO_URL  — nfo-service URL (default: http://localhost:8080)

NFO_URL="${NFO_URL:-http://localhost:8080}"

# --- Fire-and-forget log entry ---
nfo_log() {
    local cmd="$1"; shift
    local args="$*"
    curl -s -X POST "$NFO_URL/log" \
        -H "Content-Type: application/json" \
        -d "{\"cmd\":\"$cmd\",\"args\":[\"$args\"],\"language\":\"bash\",\"env\":\"${NFO_ENV:-prod}\"}" \
        >/dev/null 2>&1 &
}

# --- Run a command and log result ---
nfo_run() {
    local cmd="$1"; shift
    local start_ms=$(($(date +%s%N) / 1000000))

    # Execute
    local output
    output=$("$cmd" "$@" 2>&1)
    local rc=$?

    local end_ms=$(($(date +%s%N) / 1000000))
    local duration=$((end_ms - start_ms))

    # Determine success
    local success="true"
    local error="null"
    if [ $rc -ne 0 ]; then
        success="false"
        error="\"exit code: $rc\""
    fi

    # Send to nfo-service
    curl -s -X POST "$NFO_URL/log" \
        -H "Content-Type: application/json" \
        -d "{
            \"cmd\": \"$cmd\",
            \"args\": [$(printf '"%s",' "$@" | sed 's/,$//')],
            \"language\": \"bash\",
            \"env\": \"${NFO_ENV:-prod}\",
            \"success\": $success,
            \"duration_ms\": $duration,
            \"output\": $(echo "$output" | head -c 1000 | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))' 2>/dev/null || echo '""'),
            \"error\": $error
        }" >/dev/null 2>&1

    # Pass through output
    echo "$output"
    return $rc
}

# --- Query logs from nfo-service ---
nfo_query() {
    local filter="${1:-}"
    curl -s "$NFO_URL/logs?limit=20${filter:+&$filter}" | python3 -m json.tool 2>/dev/null
}

# --- Example usage (run this script directly) ---
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "=== nfo Bash Client Example ==="
    echo "NFO_URL=$NFO_URL"
    echo

    echo "--- Sending log entries ---"
    nfo_log "deploy" prod
    echo "Sent: deploy prod"

    nfo_log "backup" daily
    echo "Sent: backup daily"

    echo
    echo "--- Running command with logging ---"
    nfo_run echo "Hello from nfo-bash"

    echo
    echo "--- Query recent logs ---"
    nfo_query

    echo
    echo "Done. All entries logged to nfo-service at $NFO_URL"
fi
