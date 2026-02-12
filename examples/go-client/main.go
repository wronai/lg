// nfo example — Go HTTP client for nfo centralized logging service.
//
// Sends log entries to nfo-service via HTTP POST.
// Pair with examples/http_service.py.
//
// Usage:
//   go run examples/go_client.go
//
// Environment:
//   NFO_URL — nfo-service URL (default: http://localhost:8080)

package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"time"
)

// LogEntry matches the nfo-service API schema.
type LogEntry struct {
	Cmd        string   `json:"cmd"`
	Args       []string `json:"args"`
	Language   string   `json:"language"`
	Env        string   `json:"env"`
	Success    *bool    `json:"success,omitempty"`
	DurationMs *float64 `json:"duration_ms,omitempty"`
	Output     string   `json:"output,omitempty"`
	Error      string   `json:"error,omitempty"`
}

// NfoClient sends log entries to the nfo HTTP service.
type NfoClient struct {
	BaseURL    string
	HTTPClient *http.Client
}

// NewNfoClient creates a client pointing at the given nfo-service URL.
func NewNfoClient(baseURL string) *NfoClient {
	return &NfoClient{
		BaseURL:    baseURL,
		HTTPClient: &http.Client{Timeout: 5 * time.Second},
	}
}

// Log sends a single log entry to nfo-service.
func (c *NfoClient) Log(entry LogEntry) error {
	data, err := json.Marshal(entry)
	if err != nil {
		return fmt.Errorf("marshal: %w", err)
	}

	resp, err := c.HTTPClient.Post(
		c.BaseURL+"/log",
		"application/json",
		bytes.NewBuffer(data),
	)
	if err != nil {
		return fmt.Errorf("post: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("nfo-service returned %d", resp.StatusCode)
	}
	return nil
}

// LogCall wraps a function execution with nfo logging.
func (c *NfoClient) LogCall(cmd string, args []string, fn func() (string, error)) error {
	start := time.Now()
	output, err := fn()
	duration := float64(time.Since(start).Milliseconds())

	success := err == nil
	entry := LogEntry{
		Cmd:        cmd,
		Args:       args,
		Language:   "go",
		Env:        getEnv("NFO_ENV", "prod"),
		Success:    &success,
		DurationMs: &duration,
		Output:     output,
	}
	if err != nil {
		entry.Error = err.Error()
	}

	return c.Log(entry)
}

func getEnv(key, fallback string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return fallback
}

func main() {
	nfoURL := getEnv("NFO_URL", "http://localhost:8080")
	client := NewNfoClient(nfoURL)

	fmt.Printf("nfo Go Client — sending to %s\n\n", nfoURL)

	// Simple log entry
	err := client.Log(LogEntry{
		Cmd:      "build",
		Args:     []string{"v1.2.3", "--release"},
		Language: "go",
		Env:      "prod",
	})
	if err != nil {
		fmt.Printf("Error: %v\n", err)
	} else {
		fmt.Println("Sent: build v1.2.3 --release")
	}

	// Wrapped function call with timing
	err = client.LogCall("process_data", []string{"input.csv"}, func() (string, error) {
		time.Sleep(50 * time.Millisecond) // simulate work
		return "processed 1000 rows", nil
	})
	if err != nil {
		fmt.Printf("Error: %v\n", err)
	} else {
		fmt.Println("Sent: process_data input.csv (with duration)")
	}

	// Error case
	err = client.LogCall("validate", []string{"bad_input"}, func() (string, error) {
		return "", fmt.Errorf("validation failed: invalid format")
	})
	if err != nil {
		fmt.Printf("Error: %v\n", err)
	} else {
		fmt.Println("Sent: validate bad_input (error logged)")
	}

	fmt.Println("\nDone. Query logs: curl", nfoURL+"/logs")
}
