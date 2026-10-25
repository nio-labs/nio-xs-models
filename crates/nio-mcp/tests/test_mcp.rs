use nio_mcp::McpServer;
use serde_json::Value;

#[test]
fn test_mcp_initialize() {
    let server = McpServer::new();
    let req = r#"{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}"#;
    let resp = server.process_line(req).expect("response");
    let val: Value = serde_json::from_str(&resp).expect("valid json");

    assert_eq!(val["jsonrpc"], "2.0");
    assert_eq!(val["id"], 1);
    assert_eq!(val["result"]["serverInfo"]["name"], "nio-mcp-server");
    assert!(val["result"]["capabilities"]["tools"].is_object());
}

#[test]
fn test_mcp_tools_list() {
    let server = McpServer::new();
    let req = r#"{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}"#;
    let resp = server.process_line(req).expect("response");
    let val: Value = serde_json::from_str(&resp).expect("valid json");

    let tools = val["result"]["tools"].as_array().expect("tools array");
    let tool_names: Vec<&str> = tools.iter().map(|t| t["name"].as_str().unwrap()).collect();

    assert!(tool_names.contains(&"viper_synthesize"));
    assert!(tool_names.contains(&"mask_sanitize"));
    assert!(tool_names.contains(&"micro_audit"));
    assert!(tool_names.contains(&"nano_route"));
    assert!(tool_names.contains(&"mini_predict_defect"));
}

#[test]
fn test_mcp_viper_synthesize_clutch() {
    let server = McpServer::new();
    let req = r#"{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"viper_synthesize","arguments":{"intent":"kill whatever process is holding port 3000"}}}"#;
    let resp = server.process_line(req).expect("response");
    let val: Value = serde_json::from_str(&resp).expect("valid json");

    let content_text = val["result"]["content"][0]["text"].as_str().expect("text");
    let inner: Value = serde_json::from_str(content_text).expect("inner json");

    assert_eq!(inner["model"], "Viper (100M)");
    assert_eq!(inner["command"], "fuser -k 3000/tcp");
    assert_eq!(inner["is_destructive"], true);
}

#[test]
fn test_mcp_mask_sanitize() {
    let server = McpServer::new();
    let req = r#"{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"mask_sanitize","arguments":{"content":"export GITHUB_TOKEN=ghp_0123456789abcdef0123456789abcdef0123"}}}"#;
    let resp = server.process_line(req).expect("response");
    let val: Value = serde_json::from_str(&resp).expect("valid json");

    let content_text = val["result"]["content"][0]["text"].as_str().expect("text");
    let inner: Value = serde_json::from_str(content_text).expect("inner json");

    assert_eq!(inner["model"], "Mask (1.1M)");
    assert!(inner["secrets_found"].as_u64().unwrap() > 0 || !inner["sanitized_content"].as_str().unwrap().contains("ghp_0123456789abcdef0123456789abcdef0123"));
}

#[test]
fn test_mcp_micro_audit_reject() {
    let server = McpServer::new();
    let req = r#"{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"micro_audit","arguments":{"action":"rm -rf / --no-preserve-root"}}}"#;
    let resp = server.process_line(req).expect("response");
    let val: Value = serde_json::from_str(&resp).expect("valid json");

    let content_text = val["result"]["content"][0]["text"].as_str().expect("text");
    let inner: Value = serde_json::from_str(content_text).expect("inner json");

    assert_eq!(inner["model"], "Micro (5.0M)");
    assert_eq!(inner["verdict"], "REJECT");
    assert_eq!(inner["is_safe"], false);
}

#[test]
fn test_mcp_nano_route_directive() {
    let server = McpServer::new();
    let req = r#"{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"nano_route","arguments":{"text":"--bash cargo check --locked"}}}"#;
    let resp = server.process_line(req).expect("response");
    let val: Value = serde_json::from_str(&resp).expect("valid json");

    let content_text = val["result"]["content"][0]["text"].as_str().expect("text");
    let inner: Value = serde_json::from_str(content_text).expect("inner json");

    assert_eq!(inner["model"], "Nano (~0.5M)");
    assert_eq!(inner["is_zero_token"], true);
    assert_eq!(inner["directive"], "--bash");
}

#[test]
fn test_mcp_mini_predict_defect() {
    let server = McpServer::new();
    let req = r#"{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"mini_predict_defect","arguments":{"diff":"fn bad() { let x = 1; x = 2; }"}}}"#;
    let resp = server.process_line(req).expect("response");
    let val: Value = serde_json::from_str(&resp).expect("valid json");

    let content_text = val["result"]["content"][0]["text"].as_str().expect("text");
    let inner: Value = serde_json::from_str(content_text).expect("inner json");

    assert_eq!(inner["model"], "Mini (7.1M)");
    assert!(inner["risk_score"].is_number());
}

#[test]
fn test_mcp_http_health_check() {
    use std::io::{Read, Write};
    use std::net::TcpStream;
    use std::sync::Arc;
    use std::thread;

    let server = Arc::new(McpServer::new());
    let port = 49152 + (std::process::id() % 1000) as u16;
    let srv_clone = Arc::clone(&server);
    thread::spawn(move || {
        let _ = nio_mcp::http::start_http_server(srv_clone, port);
    });

    thread::sleep(std::time::Duration::from_millis(50));

    if let Ok(mut stream) = TcpStream::connect(format!("127.0.0.1:{port}")) {
        stream.write_all(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n").unwrap();
        let mut response = String::new();
        let _ = stream.read_to_string(&mut response);
        assert!(response.contains("200 OK"));
        assert!(response.contains("nioxs-mcp"));
    }
}
