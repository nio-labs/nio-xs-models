pub mod http;
pub mod protocol;
pub mod tools;

use protocol::{JsonRpcRequest, JsonRpcResponse};
use serde_json::{json, Value};
use tools::ToolRegistry;

pub struct McpServer {
    registry: ToolRegistry,
}

impl Default for McpServer {
    fn default() -> Self {
        Self::new()
    }
}

impl McpServer {
    pub fn new() -> Self {
        Self {
            registry: ToolRegistry::new(),
        }
    }

    pub fn handle_request(&self, req: JsonRpcRequest) -> Option<JsonRpcResponse> {
        let id = req.id.clone().unwrap_or(Value::Null);

        match req.method.as_str() {
            "initialize" => {
                let result = json!({
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {
                            "listChanged": false
                        }
                    },
                    "serverInfo": {
                        "name": "nio-mcp-server",
                        "version": "0.2.5"
                    }
                });
                Some(JsonRpcResponse::success(id, result))
            }
            "notifications/initialized" => {
                // Client confirmed initialization. No response needed for notifications.
                None
            }
            "ping" => {
                Some(JsonRpcResponse::success(id, json!({})))
            }
            "tools/list" => {
                let tools = self.registry.list_tools();
                let result = json!({
                    "tools": tools
                });
                Some(JsonRpcResponse::success(id, result))
            }
            "tools/call" => {
                let params = match req.params {
                    Some(Value::Object(map)) => map,
                    _ => {
                        return Some(JsonRpcResponse::error(
                            id,
                            -32602,
                            "Invalid params: expected object",
                        ));
                    }
                };

                let name = match params.get("name").and_then(|v| v.as_str()) {
                    Some(n) => n,
                    None => {
                        return Some(JsonRpcResponse::error(
                            id,
                            -32602,
                            "Missing 'name' in tool call",
                        ));
                    }
                };

                let empty_args = json!({});
                let arguments = params.get("arguments").unwrap_or(&empty_args);

                let tool_result = self.registry.call_tool(name, arguments);
                let result = json!({
                    "content": tool_result.content,
                    "isError": tool_result.is_error.unwrap_or(false)
                });

                Some(JsonRpcResponse::success(id, result))
            }
            _ => Some(JsonRpcResponse::error(
                id,
                -32601,
                format!("Method not found: {}", req.method),
            )),
        }
    }

    pub fn process_line(&self, line: &str) -> Option<String> {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            return None;
        }

        // Handle JSON-RPC payload
        match serde_json::from_str::<JsonRpcRequest>(trimmed) {
            Ok(req) => {
                let resp = self.handle_request(req)?;
                serde_json::to_string(&resp).ok()
            }
            Err(e) => {
                let err_resp = JsonRpcResponse::error(Value::Null, -32700, format!("Parse error: {e}"));
                serde_json::to_string(&err_resp).ok()
            }
        }
    }
}
