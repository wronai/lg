# Go Client

Go HTTP client for the nfo centralized logging service.

## What it shows

- **`NfoLog()`** — send a log entry to nfo-service via HTTP POST
- **`NfoLogBatch()`** — send multiple entries in one request
- **`NfoQuery()`** — query logs from the service
- Configurable via `NFO_URL` environment variable

## Prerequisites

Start the HTTP service first:

```bash
python examples/http-service/main.py
```

## Run

```bash
cd examples/go-client
go run main.go
```

## Key code

```go
type LogEntry struct {
    Cmd  string   `json:"cmd"`
    Args []string `json:"args"`
    Lang string   `json:"language"`
}

func NfoLog(cmd string, args ...string) {
    entry := LogEntry{Cmd: cmd, Args: args, Lang: "go"}
    jsonData, _ := json.Marshal(entry)
    http.Post(nfoURL+"/log", "application/json",
              bytes.NewBuffer(jsonData))
}
```
