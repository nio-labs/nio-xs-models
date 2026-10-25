use std::io::{BufRead, BufReader, Read, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::Arc;
use std::thread;

use crate::McpServer;
use crate::protocol::JsonRpcRequest;
use serde_json::json;

pub fn start_http_server(server: Arc<McpServer>, port: u16) -> anyhow::Result<()> {
    let addr = format!("127.0.0.1:{port}");
    let listener = TcpListener::bind(&addr)?;
    println!("Nio Localhost MCP HTTP/SSE server listening on http://{addr}");
    println!("  • SSE Endpoint:  http://{addr}/sse");
    println!("  • JSON-RPC POST: http://{addr}/message");
    println!("  • Health Check:  http://{addr}/health");

    for stream in listener.incoming() {
        let stream = match stream {
            Ok(s) => s,
            Err(_) => continue,
        };

        let server_clone = Arc::clone(&server);
        thread::spawn(move || {
            let _ = handle_client(stream, server_clone);
        });
    }

    Ok(())
}

fn handle_client(mut stream: TcpStream, server: Arc<McpServer>) -> anyhow::Result<()> {
    let mut reader = BufReader::new(stream.try_clone()?);
    let mut request_line = String::new();
    if reader.read_line(&mut request_line)? == 0 {
        return Ok(());
    }

    let parts: Vec<&str> = request_line.split_whitespace().collect();
    if parts.len() < 2 {
        return Ok(());
    }

    let method = parts[0];
    let path = parts[1];

    // Read headers
    let mut content_length: usize = 0;
    loop {
        let mut header_line = String::new();
        if reader.read_line(&mut header_line)? == 0 {
            break;
        }
        let trimmed = header_line.trim();
        if trimmed.is_empty() {
            break;
        }
        if trimmed.to_lowercase().starts_with("content-length:") {
            if let Some(val) = trimmed.split(':').nth(1) {
                content_length = val.trim().parse().unwrap_or(0);
            }
        }
    }

    // CORS preflight
    if method == "OPTIONS" {
        let response = concat!(
            "HTTP/1.1 200 OK\r\n",
            "Access-Control-Allow-Origin: *\r\n",
            "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n",
            "Access-Control-Allow-Headers: Content-Type, Authorization\r\n",
            "Content-Length: 0\r\n",
            "\r\n"
        );
        stream.write_all(response.as_bytes())?;
        stream.flush()?;
        return Ok(());
    }

    // Health check endpoint
    if method == "GET" && (path == "/health" || path == "/") {
        let payload = json!({
            "status": "healthy",
            "server": "nioxs-mcp",
            "version": "0.1.0",
            "protocol": "Model Context Protocol (2024-11-05)",
            "models": {
                "viper": "Viper (100M Tactical Terminal & DevOps Reflex)",
                "nano": "Nano (~0.5M Intent Reflex & Directives)",
                "micro": "Micro (5.0M Contextual Policy Arbiter)",
                "mask": "Mask (1.1M Real-Time Secret & PII Redactor)",
                "mini": "Mini (7.1M Pre-emptive Defect Forecaster)"
            }
        });
        let body = serde_json::to_string_pretty(&payload)?;
        let response = format!(
            "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: {}\r\n\r\n{}",
            body.len(),
            body
        );
        stream.write_all(response.as_bytes())?;
        stream.flush()?;
        return Ok(());
    }

    // SSE endpoint
    if method == "GET" && path.starts_with("/sse") {
        let header = concat!(
            "HTTP/1.1 200 OK\r\n",
            "Content-Type: text/event-stream\r\n",
            "Cache-Control: no-cache\r\n",
            "Connection: keep-alive\r\n",
            "Access-Control-Allow-Origin: *\r\n",
            "\r\n"
        );
        stream.write_all(header.as_bytes())?;
        let event = "event: endpoint\ndata: /message?sessionId=nio-session-local\n\n";
        stream.write_all(event.as_bytes())?;
        stream.flush()?;

        // Keep SSE connection alive with heartbeats
        loop {
            thread::sleep(std::time::Duration::from_secs(15));
            if stream.write_all(b": ping\n\n").is_err() {
                break;
            }
            let _ = stream.flush();
        }
        return Ok(());
    }

    // JSON-RPC message endpoint
    if method == "POST" && (path.starts_with("/message") || path == "/rpc" || path == "/") {
        let mut body_bytes = vec![0u8; content_length];
        reader.read_exact(&mut body_bytes)?;
        let body_str = String::from_utf8_lossy(&body_bytes);

        if let Ok(req) = serde_json::from_str::<JsonRpcRequest>(&body_str) {
            let resp = server.handle_request(req);
            let resp_json = match resp {
                Some(r) => serde_json::to_string(&r)?,
                None => json!({ "jsonrpc": "2.0", "result": null }).to_string(),
            };
            let response = format!(
                "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: {}\r\n\r\n{}",
                resp_json.len(),
                resp_json
            );
            stream.write_all(response.as_bytes())?;
            stream.flush()?;
            return Ok(());
        }
    }

    // Default 404
    let not_found = "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n";
    stream.write_all(not_found.as_bytes())?;
    stream.flush()?;
    Ok(())
}
