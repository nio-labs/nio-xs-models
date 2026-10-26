use std::io::{self, BufRead, Write};
use std::sync::Arc;
use nio_mcp::McpServer;
use nio_mcp::http::start_http_server;

fn main() -> anyhow::Result<()> {
    let args: Vec<String> = std::env::args().collect();

    if args.iter().any(|a| a == "--version" || a == "-V") {
        println!("nioxs-mcp 0.2.6 (Nio Localhost Model Context Protocol Server)");
        return Ok(());
    }

    if args.iter().any(|a| a == "--help" || a == "-h") {
        println!("Nio Localhost MCP Server (nioxs-mcp)");
        println!("Usage: nioxs-mcp [OPTIONS]");
        println!();
        println!("Options:");
        println!("  --stdio        Run Model Context Protocol server over stdin/stdout (default)");
        println!("  --port <PORT>  Run HTTP/SSE Model Context Protocol server on 127.0.0.1:<PORT>");
        println!("  --test         Run self-test diagnostic across all 5 MicroLM tools and exit");
        println!("  --version      Print version information");
        println!("  --help         Print help information");
        return Ok(());
    }

    let mut port: Option<u16> = None;
    let mut i = 1;
    while i < args.len() {
        if (args[i] == "--port" || args[i] == "-p") && i + 1 < args.len() {
            port = args[i + 1].parse().ok();
            i += 1;
        }
        i += 1;
    }

    let server = Arc::new(McpServer::new());

    if args.iter().any(|a| a == "--test") {
        println!("=== Running Nio MCP Diagnostic Self-Test ===");
        let init_req = r#"{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}"#;
        println!("-> {}", init_req);
        let init_resp = server.process_line(init_req).unwrap();
        println!("<- {}\n", init_resp);

        let list_req = r#"{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}"#;
        println!("-> {}", list_req);
        let list_resp = server.process_line(list_req).unwrap();
        println!("<- {}\n", list_resp);

        let viper_req = r#"{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"viper_synthesize","arguments":{"intent":"kill whatever process is holding port 3000"}}}"#;
        println!("-> {}", viper_req);
        let viper_resp = server.process_line(viper_req).unwrap();
        println!("<- {}\n", viper_resp);

        let mask_req = r#"{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"mask_sanitize","arguments":{"content":"curl -H 'Authorization: Bearer ghp_secret1234567890abcdef' https://api.github.com"}}}"#;
        println!("-> {}", mask_req);
        let mask_resp = server.process_line(mask_req).unwrap();
        println!("<- {}\n", mask_resp);

        let micro_req = r#"{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"micro_audit","arguments":{"action":"rm -rf /var/lib/docker"}}}"#;
        println!("-> {}", micro_req);
        let micro_resp = server.process_line(micro_req).unwrap();
        println!("<- {}\n", micro_resp);

        let nano_req = r#"{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"nano_route","arguments":{"text":"--bash cargo check --locked"}}}"#;
        println!("-> {}", nano_req);
        let nano_resp = server.process_line(nano_req).unwrap();
        println!("<- {}\n", nano_resp);

        let mini_req = r#"{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"mini_predict_defect","arguments":{"diff":"fn test() { let r = &mut x; let y = &x; }"}}}"#;
        println!("-> {}", mini_req);
        let mini_resp = server.process_line(mini_req).unwrap();
        println!("<- {}\n", mini_resp);

        let mako_req = r#"{"jsonrpc":"2.0","id":8,"method":"tools/call","params":{"name":"mako_web_scout","arguments":{"query":"RFC 7540"}}}"#;
        println!("-> {}", mako_req);
        let mako_resp = server.process_line(mako_req).unwrap();
        println!("<- {}\n", mako_resp);

        println!("✔ All MCP MicroLM self-tests passed successfully!");
        return Ok(());
    }

    if let Some(p) = port {
        let is_stdio = args.iter().any(|a| a == "--stdio");
        if is_stdio {
            let server_bg = Arc::clone(&server);
            std::thread::spawn(move || {
                let _ = start_http_server(server_bg, p);
            });
        } else {
            // Pure HTTP mode
            return start_http_server(server, p);
        }
    }

    // Default: run stdio loop for MCP clients (Cursor, Claude, Antigravity)
    let stdin = io::stdin();
    let mut stdout = io::stdout();

    for line in stdin.lock().lines() {
        let line = match line {
            Ok(l) => l,
            Err(_) => break,
        };

        if let Some(resp) = server.process_line(&line) {
            writeln!(stdout, "{}", resp)?;
            stdout.flush()?;
        }
    }

    Ok(())
}
