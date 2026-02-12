// nfo example — Rust HTTP client for nfo centralized logging service.
//
// Sends log entries to nfo-service via HTTP POST using reqwest.
// Pair with examples/http_service.py.
//
// Dependencies (Cargo.toml):
//   [dependencies]
//   reqwest = { version = "0.12", features = ["json"] }
//   serde = { version = "1", features = ["derive"] }
//   serde_json = "1"
//   tokio = { version = "1", features = ["full"] }
//
// Usage:
//   cargo run --example rust_client
//
// Environment:
//   NFO_URL — nfo-service URL (default: http://localhost:8080)

use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::env;
use std::time::Instant;

#[derive(Serialize)]
struct LogEntry<'a> {
    cmd: &'a str,
    args: Vec<&'a str>,
    language: &'a str,
    env: &'a str,
    #[serde(skip_serializing_if = "Option::is_none")]
    success: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    duration_ms: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    output: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}

#[derive(Deserialize, Debug)]
struct LogResponse {
    stored: Option<bool>,
    cmd: Option<String>,
}

/// NfoClient sends log entries to the nfo HTTP service.
struct NfoClient {
    base_url: String,
    client: Client,
}

impl NfoClient {
    fn new(base_url: &str) -> Self {
        Self {
            base_url: base_url.to_string(),
            client: Client::new(),
        }
    }

    /// Send a single log entry to nfo-service.
    async fn log(&self, entry: &LogEntry<'_>) -> Result<(), reqwest::Error> {
        self.client
            .post(format!("{}/log", self.base_url))
            .json(entry)
            .send()
            .await?;
        Ok(())
    }

    /// Wrap a function execution with nfo logging and timing.
    async fn log_call<F>(
        &self,
        cmd: &str,
        args: Vec<&str>,
        f: F,
    ) -> Result<String, Box<dyn std::error::Error>>
    where
        F: FnOnce() -> Result<String, Box<dyn std::error::Error>>,
    {
        let start = Instant::now();
        let result = f();
        let duration_ms = start.elapsed().as_secs_f64() * 1000.0;

        let nfo_env = env::var("NFO_ENV").unwrap_or_else(|_| "prod".to_string());

        let (success, output, error) = match &result {
            Ok(out) => (true, Some(out.clone()), None),
            Err(e) => (false, None, Some(e.to_string())),
        };

        let entry = LogEntry {
            cmd,
            args,
            language: "rust",
            env: &nfo_env,
            success: Some(success),
            duration_ms: Some(duration_ms),
            output,
            error,
        };

        let _ = self.log(&entry).await;
        result
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let nfo_url =
        env::var("NFO_URL").unwrap_or_else(|_| "http://localhost:8080".to_string());
    let client = NfoClient::new(&nfo_url);

    println!("nfo Rust Client — sending to {}\n", nfo_url);

    // Simple log entry
    let entry = LogEntry {
        cmd: "compile",
        args: vec!["--release", "--target", "x86_64"],
        language: "rust",
        env: "prod",
        success: Some(true),
        duration_ms: Some(1234.5),
        output: Some("compiled successfully".to_string()),
        error: None,
    };
    client.log(&entry).await?;
    println!("Sent: compile --release --target x86_64");

    // Wrapped function call with timing
    let result = client
        .log_call("process_data", vec!["input.csv"], || {
            std::thread::sleep(std::time::Duration::from_millis(50));
            Ok("processed 1000 rows".to_string())
        })
        .await?;
    println!("Sent: process_data input.csv -> {}", result);

    // Error case
    let _ = client
        .log_call("validate", vec!["bad_input"], || {
            Err("validation failed: invalid format".into())
        })
        .await;
    println!("Sent: validate bad_input (error logged)");

    println!("\nDone. Query logs: curl {}/logs", nfo_url);
    Ok(())
}
