use serde::{Deserialize, Serialize};
use std::net::{Ipv4Addr, Ipv6Addr};
use std::sync::Mutex;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RedactedSpan {
    pub category: String,
    pub start: usize,
    pub end: usize,
    pub original_sample: String,
}

#[derive(Debug, Clone)]
struct InternalSpan {
    category: String,
    start: usize,
    end: usize,
    original_sample: String,
    replacement: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RedactionResult {
    pub model: String,
    #[serde(skip)]
    pub original: String,
    pub sanitized: String,
    pub risk_score: f32,
    pub is_clean: bool,
    pub redacted_count: usize,
    pub spans: Vec<RedactedSpan>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct YamlBlockState {
    pub parent_indent: usize,
    pub block_indent: Option<usize>,
    pub is_block_scalar: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct AwaitingPasswordState {
    pub parent_indent: usize,
    pub is_env: bool,
}

// Tracks a redacted JSON value without retaining its plaintext across chunks.
#[derive(Debug, Clone)]
struct JsonSecretState {
    depth: usize,
    in_string: bool,
    escaped: bool,
    container: bool,
}

impl JsonSecretState {
    fn new(first: u8) -> Self {
        Self {
            depth: 0,
            in_string: false,
            escaped: false,
            container: matches!(first, b'{' | b'['),
        }
    }

    // Returns the end of a container, or the delimiter before a primitive.
    fn consume(&mut self, bytes: &[u8]) -> (usize, bool) {
        for (i, &b) in bytes.iter().enumerate() {
            if !self.container {
                if b.is_ascii_whitespace() || matches!(b, b',' | b'}' | b']') {
                    return (i, true);
                }
            } else if self.in_string {
                if self.escaped {
                    self.escaped = false;
                } else if b == b'\\' {
                    self.escaped = true;
                } else if b == b'"' {
                    self.in_string = false;
                }
            } else {
                match b {
                    b'"' => self.in_string = true,
                    b'{' | b'[' => self.depth += 1,
                    b'}' | b']' => {
                        self.depth = self.depth.saturating_sub(1);
                        if self.depth == 0 {
                            return (i + 1, true);
                        }
                    }
                    _ => {}
                }
            }
        }
        (bytes.len(), false)
    }
}

#[derive(Default)]
struct StreamState {
    buffer: String,
    recent_emitted: String,
    emitted_prefix_len: usize,
    in_secret_token: bool,
    in_unquoted_secret: bool,
    json_secret: Option<JsonSecretState>,
    in_double_quote_secret: bool,
    in_single_quote_secret: bool,
    awaiting_double_quote_close: bool,
    awaiting_single_quote_close: bool,
    awaiting_password: Option<AwaitingPasswordState>,
    awaiting_email: bool,
    awaiting_host: bool,
    ended_in_pem: bool,
    ended_in_ip: bool,
    ended_in_ipv6: bool,
    yaml_block: Option<YamlBlockState>,
}

pub struct NioMask {
    pub model_name: String,
    state: Mutex<StreamState>,
}

impl Default for NioMask {
    fn default() -> Self {
        Self::new()
    }
}

impl NioMask {
    pub fn new() -> Self {
        Self {
            model_name: "nioxs::nio-mask".to_string(),
            state: Mutex::new(StreamState::default()),
        }
    }

    /// Explicit end-of-input processing: flushes and redacts any remaining buffered content.
    pub fn finish(&self) -> RedactionResult {
        let mut st = self.state.lock().unwrap();
        let prev = std::mem::take(&mut st.buffer);
        let mut working = prev.clone();

        let mut output_prefix = String::new();
        let mut extra_spans = Vec::new();
        let mut extra_risk = 0.0f32;

        if st.awaiting_password.is_some() || st.in_unquoted_secret || st.in_double_quote_secret || st.in_single_quote_secret {
            if !working.is_empty() {
                if working.starts_with('"') && working.ends_with('"') && working.len() >= 2 {
                    output_prefix.push_str("\"[REDACTED_SECRET]\"");
                } else if working.starts_with('\'') && working.ends_with('\'') && working.len() >= 2 {
                    output_prefix.push_str("'[REDACTED_SECRET]'");
                } else if working.starts_with('"') {
                    output_prefix.push_str("\"[REDACTED_SECRET]");
                } else if working.starts_with('\'') {
                    output_prefix.push_str("'[REDACTED_SECRET]");
                } else {
                    output_prefix.push_str("[REDACTED_SECRET]");
                }
                extra_spans.push(RedactedSpan {
                    category: "SECRET".to_string(),
                    start: 0,
                    end: output_prefix.len(),
                    original_sample: "[REDACTED_PASSWORD]".to_string(),
                });
                extra_risk = extra_risk.max(1.0);
                working.clear();
            }
        }

        let yaml_block = st.yaml_block.take();
        let emitted_prefix_len = st.emitted_prefix_len;
        st.recent_emitted.clear();
        st.in_secret_token = false;
        st.in_unquoted_secret = false;
        st.json_secret = None;
        st.in_double_quote_secret = false;
        st.in_single_quote_secret = false;
        st.awaiting_double_quote_close = false;
        st.awaiting_single_quote_close = false;
        st.awaiting_password = None;
        st.awaiting_email = false;
        st.awaiting_host = false;
        st.ended_in_pem = false;
        st.ended_in_ip = false;
        st.ended_in_ipv6 = false;
        st.emitted_prefix_len = 0;

        if working.is_empty() && output_prefix.is_empty() {
            return RedactionResult {
                model: self.model_name.clone(),
                original: prev,
                sanitized: String::new(),
                risk_score: 0.0,
                is_clean: true,
                redacted_count: 0,
                spans: Vec::new(),
            };
        }

        let (sanitized_body, mut spans, risk_score, _, _, _, _, _, _, _) = self.scan_and_redact(&working, yaml_block);
        let prefix_len = output_prefix.len();
        if prefix_len > 0 {
            for span in &mut spans {
                span.start += prefix_len;
                span.end += prefix_len;
            }
            extra_spans.append(&mut spans);
            spans = extra_spans;
        }

        let final_risk = risk_score.max(extra_risk);
        let mut sanitized = format!("{}{}", output_prefix, sanitized_body);
        if emitted_prefix_len > 0 {
            if sanitized.len() >= emitted_prefix_len {
                sanitized = sanitized[emitted_prefix_len..].to_string();
                for span in &mut spans {
                    if span.start >= emitted_prefix_len {
                        span.start -= emitted_prefix_len;
                        span.end = span.end.saturating_sub(emitted_prefix_len);
                    }
                }
            } else {
                sanitized.clear();
            }
        }
        let is_clean = spans.is_empty() && output_prefix.is_empty();

        RedactionResult {
            model: self.model_name.clone(),
            original: prev,
            sanitized,
            risk_score: final_risk,
            is_clean,
            redacted_count: spans.len(),
            spans,
        }
    }

    /// Redacts high-entropy secrets and sensitive PII from a stream chunk.
    pub fn sanitize(&self, chunk: &str) -> RedactionResult {
        let mut st = self.state.lock().unwrap();
        let prev = std::mem::take(&mut st.buffer);
        let mut working = format!("{}{}", prev, chunk);

        // A placeholder was already emitted for this value. Consume only its
        // continuation, keeping the JSON separator and following public fields.
        if let Some(mut json_secret) = st.json_secret.take() {
            let (end, closed) = json_secret.consume(working.as_bytes());
            working = working[end..].to_string();
            if !closed {
                st.json_secret = Some(json_secret);
            }
            st.recent_emitted.clear();
        }

        let mut emitted_prefix_len = st.emitted_prefix_len;
        st.emitted_prefix_len = 0;
        let prev_recent = std::mem::take(&mut st.recent_emitted);
        if emitted_prefix_len == 0 && !prev_recent.is_empty() && !working.is_empty() {
            if let Some(best_split) = Self::find_split_attachment(&prev_recent, &working) {
                let prefix_to_attach = &prev_recent[prev_recent.len() - best_split..];
                working = format!("{}{}", prefix_to_attach, working);
                emitted_prefix_len += best_split;
                st.awaiting_password = None;
            }
        }

        let mut output_prefix = String::new();
        let mut extra_spans = Vec::new();
        let mut extra_risk = 0.0f32;

        // 0. If previous chunk ended in a redacted IP octet without newline, consume continuation digits
        if st.ended_in_ip {
            let digits_len = working.chars().take_while(|c| c.is_ascii_digit()).count();
            if digits_len > 0 {
                working = working[digits_len..].to_string();
            }
            if !working.is_empty() {
                st.ended_in_ip = false;
            }
        }

        // 0b. If previous chunk ended in a redacted IPv6 without newline, consume continuation hex digits or colons
        if st.ended_in_ipv6 {
            let hex_len = working.chars().take_while(|c| c.is_ascii_hexdigit() || *c == ':').count();
            if hex_len > 0 {
                working = working[hex_len..].to_string();
            }
            if !working.is_empty() {
                st.ended_in_ipv6 = false;
            }
        }

        // 1. If previous chunk ended in a PEM block closing dashes without newline, consume leading newline
        if st.ended_in_pem {
            st.ended_in_pem = false;
            if working.starts_with("\r\n") {
                working = working[2..].to_string();
            } else if working.starts_with('\n') {
                working = working[1..].to_string();
            }
        }

        // 2. Secret token continuation (e.g. ghp_...)
        if st.in_secret_token && !chunk.is_empty() {
            let token_end = working.find(|c: char| {
                c.is_whitespace() || c == '\'' || c == '"' || c == '`' || c == ';' || c == ',' || c == '}' || c == ')' || c == ']'
            });
            if let Some(pos) = token_end {
                working = working[pos..].to_string();
                st.in_secret_token = false;
            } else {
                working.clear();
            }
        }

        // 3. Unquoted secret value continuation (after password=, GITHUB_TOKEN=, etc.)
        if st.in_unquoted_secret && !chunk.is_empty() {
            if let Some(pos) = working.find(|c| c == '\r' || c == '\n') {
                working = working[pos..].to_string();
                st.in_unquoted_secret = false;
            } else {
                working.clear();
            }
        }

        // 4. Double-quoted secret continuation (opening quote already emitted)
        if st.in_double_quote_secret && !chunk.is_empty() {
            let mut close_quote = None;
            let mut escaped = false;
            for (idx, ch) in working.char_indices() {
                if escaped {
                    escaped = false;
                } else if ch == '\\' {
                    escaped = true;
                } else if ch == '"' {
                    close_quote = Some(idx);
                    break;
                }
            }
            if let Some(pos) = close_quote {
                output_prefix.push_str("[REDACTED_SECRET]\"");
                extra_spans.push(RedactedSpan {
                    category: "SECRET".to_string(),
                    start: 0,
                    end: output_prefix.len(),
                    original_sample: "[REDACTED_PASSWORD]".to_string(),
                });
                extra_risk = extra_risk.max(1.0);
                working = working[pos + 1..].to_string();
                st.in_double_quote_secret = false;
            } else {
                st.buffer = working;
                return RedactionResult {
                    model: self.model_name.clone(),
                    original: chunk.to_string(),
                    sanitized: String::new(),
                    risk_score: 0.0,
                    is_clean: true,
                    redacted_count: 0,
                    spans: Vec::new(),
                };
            }
        }

        // 4b. Double-quoted secret continuation (opening quote NOT emitted yet)
        if st.awaiting_double_quote_close && !chunk.is_empty() {
            let mut close_quote = None;
            let mut escaped = false;
            for (idx, ch) in working.char_indices() {
                if escaped {
                    escaped = false;
                } else if ch == '\\' {
                    escaped = true;
                } else if ch == '"' {
                    close_quote = Some(idx);
                    break;
                }
            }
            if let Some(pos) = close_quote {
                output_prefix.push_str("\"[REDACTED_SECRET]\"");
                extra_spans.push(RedactedSpan {
                    category: "SECRET".to_string(),
                    start: 0,
                    end: output_prefix.len(),
                    original_sample: "[REDACTED_PASSWORD]".to_string(),
                });
                extra_risk = extra_risk.max(1.0);
                working = working[pos + 1..].to_string();
                st.awaiting_double_quote_close = false;
            } else {
                st.buffer = working;
                return RedactionResult {
                    model: self.model_name.clone(),
                    original: chunk.to_string(),
                    sanitized: String::new(),
                    risk_score: 0.0,
                    is_clean: true,
                    redacted_count: 0,
                    spans: Vec::new(),
                };
            }
        }

        // 5. Single-quoted secret continuation (opening quote already emitted)
        if st.in_single_quote_secret && !chunk.is_empty() {
            let bytes = working.as_bytes();
            let mut close_quote = None;
            let mut i = 0;
            while i < bytes.len() {
                if bytes[i] == b'\\' && i + 1 < bytes.len() {
                    i += 2;
                } else if bytes[i] == b'\'' {
                    if i + 1 < bytes.len() && bytes[i + 1] == b'\'' {
                        i += 2;
                    } else if i + 1 == bytes.len() {
                        break;
                    } else {
                        close_quote = Some(i);
                        break;
                    }
                } else {
                    i += 1;
                }
            }
            if let Some(pos) = close_quote {
                output_prefix.push_str("[REDACTED_SECRET]'");
                extra_spans.push(RedactedSpan {
                    category: "SECRET".to_string(),
                    start: 0,
                    end: output_prefix.len(),
                    original_sample: "[REDACTED_PASSWORD]".to_string(),
                });
                extra_risk = extra_risk.max(1.0);
                working = working[pos + 1..].to_string();
                st.in_single_quote_secret = false;
            } else {
                st.buffer = working;
                return RedactionResult {
                    model: self.model_name.clone(),
                    original: chunk.to_string(),
                    sanitized: String::new(),
                    risk_score: 0.0,
                    is_clean: true,
                    redacted_count: 0,
                    spans: Vec::new(),
                };
            }
        }

        // 5b. Single-quoted secret continuation (opening quote NOT emitted yet)
        if st.awaiting_single_quote_close && !chunk.is_empty() {
            let bytes = working.as_bytes();
            let mut close_quote = None;
            let mut i = 0;
            while i < bytes.len() {
                if bytes[i] == b'\\' && i + 1 < bytes.len() {
                    i += 2;
                } else if bytes[i] == b'\'' {
                    if i + 1 < bytes.len() && bytes[i + 1] == b'\'' {
                        i += 2;
                    } else if i + 1 == bytes.len() {
                        break;
                    } else {
                        close_quote = Some(i);
                        break;
                    }
                } else {
                    i += 1;
                }
            }
            if let Some(pos) = close_quote {
                output_prefix.push_str("'[REDACTED_SECRET]'");
                extra_spans.push(RedactedSpan {
                    category: "SECRET".to_string(),
                    start: 0,
                    end: output_prefix.len(),
                    original_sample: "[REDACTED_PASSWORD]".to_string(),
                });
                extra_risk = extra_risk.max(1.0);
                working = working[pos + 1..].to_string();
                st.awaiting_single_quote_close = false;
            } else {
                st.buffer = working;
                return RedactionResult {
                    model: self.model_name.clone(),
                    original: chunk.to_string(),
                    sanitized: String::new(),
                    risk_score: 0.0,
                    is_clean: true,
                    redacted_count: 0,
                    spans: Vec::new(),
                };
            }
        }

        // 6. Awaiting secret value after key= or key:
        if let Some(pw_st) = st.awaiting_password {
            if !working.is_empty() {
                let leading_spaces = working.len() - working.trim_start_matches(|c| c == ' ' || c == '\t').len();
                if leading_spaces > 0 {
                    output_prefix.push_str(&working[..leading_spaces]);
                    working = working[leading_spaces..].to_string();
                }
                if working.starts_with('"') {
                    let mut close_quote = None;
                    let mut escaped = false;
                    for (idx, ch) in working[1..].char_indices() {
                        if escaped {
                            escaped = false;
                        } else if ch == '\\' {
                            escaped = true;
                        } else if ch == '"' {
                            close_quote = Some(1 + idx);
                            break;
                        }
                    }
                    if let Some(pos) = close_quote {
                        output_prefix.push_str("\"[REDACTED_SECRET]\"");
                        extra_spans.push(RedactedSpan {
                            category: "SECRET".to_string(),
                            start: 0,
                            end: output_prefix.len(),
                            original_sample: "[REDACTED_PASSWORD]".to_string(),
                        });
                        extra_risk = extra_risk.max(1.0);
                        working = working[pos + 1..].to_string();
                        st.awaiting_password = None;
                    } else {
                        st.buffer = working;
                        return RedactionResult {
                            model: self.model_name.clone(),
                            original: chunk.to_string(),
                            sanitized: String::new(),
                            risk_score: 0.0,
                            is_clean: true,
                            redacted_count: 0,
                            spans: Vec::new(),
                        };
                    }
                } else if working.starts_with('\'') {
                    let bytes = working.as_bytes();
                    let mut close_quote = None;
                    let mut i = 1;
                    while i < bytes.len() {
                        if bytes[i] == b'\\' && i + 1 < bytes.len() {
                            i += 2;
                        } else if bytes[i] == b'\'' {
                            if i + 1 < bytes.len() && bytes[i + 1] == b'\'' {
                                i += 2;
                            } else if i + 1 == bytes.len() {
                                break;
                            } else {
                                close_quote = Some(i);
                                break;
                            }
                        } else {
                            i += 1;
                        }
                    }
                    if let Some(pos) = close_quote {
                        output_prefix.push_str("'[REDACTED_SECRET]'");
                        extra_spans.push(RedactedSpan {
                            category: "SECRET".to_string(),
                            start: 0,
                            end: output_prefix.len(),
                            original_sample: "[REDACTED_PASSWORD]".to_string(),
                        });
                        extra_risk = extra_risk.max(1.0);
                        working = working[pos + 1..].to_string();
                        st.awaiting_password = None;
                    } else {
                        st.buffer = working;
                        return RedactionResult {
                            model: self.model_name.clone(),
                            original: chunk.to_string(),
                            sanitized: String::new(),
                            risk_score: 0.0,
                            is_clean: true,
                            redacted_count: 0,
                            spans: Vec::new(),
                        };
                    }
                } else if pw_st.is_env {
                    let secret_start = output_prefix.len();
                    output_prefix.push_str("[REDACTED_SECRET]");
                    extra_spans.push(RedactedSpan {
                        category: "SECRET".to_string(),
                        start: secret_start,
                        end: output_prefix.len(),
                        original_sample: "[REDACTED_PASSWORD]".to_string(),
                    });
                    extra_risk = extra_risk.max(1.0);
                    st.awaiting_password = None;
                    if let Some(nl) = working.find('\n') {
                        working = working[nl..].to_string();
                    } else {
                        working.clear();
                        st.in_unquoted_secret = true;
                    }
                } else {
                    let p_indent = pw_st.parent_indent;
                    let trimmed = working.trim_start_matches(|c| c == ' ' || c == '\t');
                    let mut prop_cursor = 0;
                    let t_bytes = trimmed.as_bytes();
                    while prop_cursor < t_bytes.len() && (t_bytes[prop_cursor] == b'!' || t_bytes[prop_cursor] == b'&') {
                        while prop_cursor < t_bytes.len() && !t_bytes[prop_cursor].is_ascii_whitespace() {
                            prop_cursor += 1;
                        }
                        while prop_cursor < t_bytes.len() && (t_bytes[prop_cursor] == b' ' || t_bytes[prop_cursor] == b'\t') {
                            prop_cursor += 1;
                        }
                    }
                    let after_props = &trimmed[prop_cursor..];
                    let is_block_scalar = after_props.starts_with('|') || after_props.starts_with('>');
                    let is_line_end = after_props.starts_with('\n') || after_props.starts_with("\r\n") || after_props.starts_with('#');

                    if is_block_scalar && working.contains('\n') {
                        let nl = working.find('\n').unwrap();
                        let header = &working[..=nl];
                        output_prefix.push_str(header);
                        let trimmed_after_bytes = after_props.as_bytes();
                        let mut c = 1;
                        let mut explicit_indent = None;
                        while c < trimmed_after_bytes.len() && (trimmed_after_bytes[c] == b'+' || trimmed_after_bytes[c] == b'-' || trimmed_after_bytes[c].is_ascii_digit()) {
                            if trimmed_after_bytes[c] >= b'1' && trimmed_after_bytes[c] <= b'9' && explicit_indent.is_none() {
                                explicit_indent = Some((trimmed_after_bytes[c] - b'0') as usize);
                            }
                            c += 1;
                        }
                        let block_indent = explicit_indent.map(|n| p_indent + n);
                        st.yaml_block = Some(YamlBlockState {
                            parent_indent: p_indent,
                            block_indent,
                            is_block_scalar: true,
                        });
                        st.awaiting_password = None;
                        working = working[nl + 1..].to_string();
                    } else if is_block_scalar && !working.contains('\n') {
                        st.buffer = working;
                        return RedactionResult {
                            model: self.model_name.clone(),
                            original: chunk.to_string(),
                            sanitized: String::new(),
                            risk_score: 0.0,
                            is_clean: true,
                            redacted_count: 0,
                            spans: Vec::new(),
                        };
                    } else if is_line_end && working.contains('\n') {
                        // Following-line YAML scalar (e.g. "password: !!str\n" or "password:\n")
                        let nl = working.find('\n').unwrap();
                        let header = &working[..=nl];
                        output_prefix.push_str(header);
                        st.yaml_block = Some(YamlBlockState {
                            parent_indent: p_indent,
                            block_indent: None,
                            is_block_scalar: false,
                        });
                        st.awaiting_password = None;
                        working = working[nl + 1..].to_string();
                    } else if prop_cursor > 0 && !working.contains('\n') && after_props.is_empty() {
                        st.buffer = working;
                        return RedactionResult {
                            model: self.model_name.clone(),
                            original: chunk.to_string(),
                            sanitized: String::new(),
                            risk_score: 0.0,
                            is_clean: true,
                            redacted_count: 0,
                            spans: Vec::new(),
                        };
                    } else if prop_cursor > 0 && after_props.starts_with('"') {
                        let prop_prefix_len = working.len() - after_props.len();
                        let mut close_quote = None;
                        let mut escaped = false;
                        for (idx, ch) in after_props[1..].char_indices() {
                            if escaped {
                                escaped = false;
                            } else if ch == '\\' {
                                escaped = true;
                            } else if ch == '"' {
                                close_quote = Some(1 + idx);
                                break;
                            }
                        }
                        if let Some(pos) = close_quote {
                            output_prefix.push_str(&working[..prop_prefix_len]);
                            let secret_start = output_prefix.len();
                            output_prefix.push_str("\"[REDACTED_SECRET]\"");
                            extra_spans.push(RedactedSpan {
                                category: "SECRET".to_string(),
                                start: secret_start,
                                end: output_prefix.len(),
                                original_sample: "[REDACTED_PASSWORD]".to_string(),
                            });
                            extra_risk = extra_risk.max(1.0);
                            working = after_props[pos + 1..].to_string();
                            st.awaiting_password = None;
                        } else {
                            st.buffer = working;
                            return RedactionResult {
                                model: self.model_name.clone(),
                                original: chunk.to_string(),
                                sanitized: String::new(),
                                risk_score: 0.0,
                                is_clean: true,
                                redacted_count: 0,
                                spans: Vec::new(),
                            };
                        }
                    } else if prop_cursor > 0 && after_props.starts_with('\'') {
                        let prop_prefix_len = working.len() - after_props.len();
                        let bytes = after_props.as_bytes();
                        let mut close_quote = None;
                        let mut i = 1;
                        while i < bytes.len() {
                            if bytes[i] == b'\\' && i + 1 < bytes.len() {
                                i += 2;
                            } else if bytes[i] == b'\'' {
                                if i + 1 < bytes.len() && bytes[i + 1] == b'\'' {
                                    i += 2;
                                } else if i + 1 == bytes.len() {
                                    break;
                                } else {
                                    close_quote = Some(i);
                                    break;
                                }
                            } else {
                                i += 1;
                            }
                        }
                        if let Some(pos) = close_quote {
                            output_prefix.push_str(&working[..prop_prefix_len]);
                            let secret_start = output_prefix.len();
                            output_prefix.push_str("'[REDACTED_SECRET]'");
                            extra_spans.push(RedactedSpan {
                                category: "SECRET".to_string(),
                                start: secret_start,
                                end: output_prefix.len(),
                                original_sample: "[REDACTED_PASSWORD]".to_string(),
                            });
                            extra_risk = extra_risk.max(1.0);
                            working = after_props[pos + 1..].to_string();
                            st.awaiting_password = None;
                        } else {
                            st.buffer = working;
                            return RedactionResult {
                                model: self.model_name.clone(),
                                original: chunk.to_string(),
                                sanitized: String::new(),
                                risk_score: 0.0,
                                is_clean: true,
                                redacted_count: 0,
                                spans: Vec::new(),
                            };
                        }
                    } else if prop_cursor > 0 && !after_props.is_empty() {
                        let prop_prefix_len = working.len() - after_props.len();
                        output_prefix.push_str(&working[..prop_prefix_len]);
                        output_prefix.push_str("[REDACTED_SECRET]");
                        extra_spans.push(RedactedSpan {
                            category: "SECRET".to_string(),
                            start: output_prefix.len() - "[REDACTED_SECRET]".len(),
                            end: output_prefix.len(),
                            original_sample: "[REDACTED_PASSWORD]".to_string(),
                        });
                        extra_risk = extra_risk.max(1.0);
                        st.awaiting_password = None;
                        let nl = after_props.find('\n');
                        if let Some(pos) = nl {
                            working = after_props[pos..].to_string();
                        } else {
                            working.clear();
                            st.in_unquoted_secret = true;
                        }
                    } else {
                        let nl = working.find('\n');
                        output_prefix.push_str("[REDACTED_SECRET]");
                        extra_spans.push(RedactedSpan {
                            category: "SECRET".to_string(),
                            start: 0,
                            end: output_prefix.len(),
                            original_sample: "[REDACTED_PASSWORD]".to_string(),
                        });
                        extra_risk = extra_risk.max(1.0);
                        st.awaiting_password = None;
                        if let Some(pos) = nl {
                            working = working[pos..].to_string();
                        } else {
                            working.clear();
                            st.in_unquoted_secret = true;
                        }
                    }
                }
            }
        }

        // 7. Awaiting host continuation
        if st.awaiting_host {
            if working.ends_with('\n') || working.parse::<Ipv4Addr>().is_ok() || working.parse::<Ipv6Addr>().is_ok() {
                st.awaiting_host = false;
            } else if !working.is_empty() {
                st.buffer = working;
                return RedactionResult {
                    model: self.model_name.clone(),
                    original: chunk.to_string(),
                    sanitized: String::new(),
                    risk_score: 0.0,
                    is_clean: true,
                    redacted_count: 0,
                    spans: Vec::new(),
                };
            }
        }

        // 8. Awaiting email continuation
        if st.awaiting_email {
            if working.ends_with('\n') || (working.contains('@') && working.contains('.')) {
                st.awaiting_email = false;
            } else if !working.is_empty() {
                st.buffer = working;
                return RedactionResult {
                    model: self.model_name.clone(),
                    original: chunk.to_string(),
                    sanitized: String::new(),
                    risk_score: 0.0,
                    is_clean: true,
                    redacted_count: 0,
                    spans: Vec::new(),
                };
            }
        }

        // Check unclosed blocks or trailing partial prefixes
        let (mut text_to_process, mut next_buf, new_awaiting_pw, new_awaiting_email, new_awaiting_host, new_in_dquote, new_in_squote) =
            self.split_stream_chunk(&working, st.yaml_block.is_some());

        // Keep the enclosing JSON separator with a buffered quoted key. It
        // identifies JSON when the key or separator spans several chunks.
        let before_key = text_to_process.trim_end();
        if next_buf.starts_with('"') && (before_key.ends_with('{') || before_key.ends_with(',')) {
            let context_start = before_key.len() - 1;
            text_to_process = &working[..context_start];
            next_buf = &working[context_start..];
        }

        if let Some(p_indent) = new_awaiting_pw {
            st.awaiting_password = Some(p_indent);
        }
        if new_awaiting_email {
            st.awaiting_email = true;
        }
        if new_awaiting_host {
            st.awaiting_host = true;
        }
        if new_in_dquote {
            st.in_double_quote_secret = true;
        }
        if new_in_squote {
            st.in_single_quote_secret = true;
        }
        if !next_buf.is_empty() {
            st.buffer = next_buf.to_string();
        }

        let (sanitized_body, mut spans, risk_score, ended_in_secret, ended_in_pem, active_yaml_block, ended_in_ip, ended_in_ipv6, ended_in_unquoted_secret, json_secret) =
            self.scan_and_redact(text_to_process, st.yaml_block.take());

        if json_secret.is_some() {
            st.json_secret = json_secret;
        }

        if ended_in_unquoted_secret {
            st.in_unquoted_secret = true;
        } else if ended_in_secret {
            st.in_secret_token = true;
        }
        if ended_in_pem {
            st.ended_in_pem = true;
        }
        if ended_in_ip {
            st.ended_in_ip = true;
        }
        if ended_in_ipv6 {
            st.ended_in_ipv6 = true;
        }
        st.yaml_block = active_yaml_block;

        let prefix_len = output_prefix.len();
        if prefix_len > 0 {
            for span in &mut spans {
                span.start += prefix_len;
                span.end += prefix_len;
            }
            extra_spans.append(&mut spans);
            spans = extra_spans;
        }

        let final_risk = risk_score.max(extra_risk);
        let mut sanitized = format!("{}{}", output_prefix, sanitized_body);
        if emitted_prefix_len > 0 {
            if sanitized.len() >= emitted_prefix_len {
                sanitized = sanitized[emitted_prefix_len..].to_string();
                for span in &mut spans {
                    if span.start >= emitted_prefix_len {
                        span.start -= emitted_prefix_len;
                        span.end = span.end.saturating_sub(emitted_prefix_len);
                    }
                }
            } else {
                st.emitted_prefix_len = emitted_prefix_len - sanitized.len();
                sanitized.clear();
            }
        }

        let is_clean = spans.is_empty() && output_prefix.is_empty();

        let full_emitted = format!("{}{}", prev_recent, sanitized);
        let mut start_idx = full_emitted.len().saturating_sub(1024);
        while !full_emitted.is_char_boundary(start_idx) {
            start_idx += 1;
        }
        st.recent_emitted = full_emitted[start_idx..].to_string();

        RedactionResult {
            model: self.model_name.clone(),
            original: chunk.to_string(),
            sanitized,
            risk_score: final_risk,
            is_clean,
            redacted_count: spans.len(),
            spans,
        }
    }

    fn is_sensitive_key(decoded: &str) -> bool {
        const PW_KEYS: &[&str] = &[
            "password", "passwd", "pwd", "secret",
            "api_key", "token", "github_token", "aws_secret_access_key",
        ];
        let lower = decoded.to_ascii_lowercase();
        PW_KEYS.contains(&lower.as_str())
    }

    fn decode_json_key(bytes: &[u8]) -> Option<(String, usize)> {
        if bytes.is_empty() || bytes[0] != b'"' {
            return None;
        }
        let mut decoded = String::new();
        let mut i = 1;
        while i < bytes.len() {
            match bytes[i] {
                b'"' => {
                    return Some((decoded, i + 1));
                }
                b'\\' => {
                    i += 1;
                    if i >= bytes.len() {
                        return None;
                    }
                    match bytes[i] {
                        b'"' => { decoded.push('"'); i += 1; }
                        b'\\' => { decoded.push('\\'); i += 1; }
                        b'/' => { decoded.push('/'); i += 1; }
                        b'b' => { decoded.push('\x08'); i += 1; }
                        b'f' => { decoded.push('\x0c'); i += 1; }
                        b'n' => { decoded.push('\n'); i += 1; }
                        b'r' => { decoded.push('\r'); i += 1; }
                        b't' => { decoded.push('\t'); i += 1; }
                        b'0' => { decoded.push('\0'); i += 1; }
                        b'a' => { decoded.push('\x07'); i += 1; }
                        b'e' => { decoded.push('\x1b'); i += 1; }
                        b'v' => { decoded.push('\x0b'); i += 1; }
                        b'\n' | b'\r' => {
                            if bytes[i] == b'\r' && bytes.get(i + 1) == Some(&b'\n') { i += 1; }
                            i += 1;
                            while i < bytes.len() && matches!(bytes[i], b' ' | b'\t') { i += 1; }
                        }
                        b'x' => {
                            i += 1;
                            if i + 2 > bytes.len() {
                                return None;
                            }
                            let hex_str = std::str::from_utf8(&bytes[i..i + 2]).ok()?;
                            let code = u8::from_str_radix(hex_str, 16).ok()?;
                            decoded.push(code as char);
                            i += 2;
                        }
                        b'u' => {
                            i += 1;
                            if i + 4 > bytes.len() {
                                return None;
                            }
                            let hex_str = std::str::from_utf8(&bytes[i..i + 4]).ok()?;
                            let code = u16::from_str_radix(hex_str, 16).ok()?;
                            i += 4;
                            if (0xD800..=0xDBFF).contains(&code) {
                                if i + 6 <= bytes.len() && bytes[i] == b'\\' && bytes[i + 1] == b'u' {
                                    let hex2_str = std::str::from_utf8(&bytes[i + 2..i + 6]).ok()?;
                                    if let Ok(code2) = u16::from_str_radix(hex2_str, 16) {
                                        if (0xDC00..=0xDFFF).contains(&code2) {
                                            let scalar = (((code as u32 - 0xD800) << 10) | (code2 as u32 - 0xDC00)) + 0x10000;
                                            if let Some(ch) = char::from_u32(scalar) {
                                                decoded.push(ch);
                                                i += 6;
                                                continue;
                                            }
                                        }
                                    }
                                }
                                decoded.push(char::REPLACEMENT_CHARACTER);
                            } else if let Some(ch) = char::from_u32(code as u32) {
                                decoded.push(ch);
                            } else {
                                decoded.push(char::REPLACEMENT_CHARACTER);
                            }
                        }
                        b'U' => {
                            i += 1;
                            if i + 8 > bytes.len() {
                                return None;
                            }
                            let hex_str = std::str::from_utf8(&bytes[i..i + 8]).ok()?;
                            let code = u32::from_str_radix(hex_str, 16).ok()?;
                            i += 8;
                            if let Some(ch) = char::from_u32(code) {
                                decoded.push(ch);
                            } else {
                                decoded.push(char::REPLACEMENT_CHARACTER);
                            }
                        }
                        _ => {
                            decoded.push(bytes[i] as char);
                            i += 1;
                        }
                    }
                }
                b => {
                    if b < 128 {
                        decoded.push(b as char);
                        i += 1;
                    } else {
                        let s = std::str::from_utf8(&bytes[i..]).ok()?;
                        let ch = s.chars().next()?;
                        decoded.push(ch);
                        i += ch.len_utf8();
                    }
                }
            }
        }
        None
    }

    fn decode_json_key_prefix(bytes: &[u8]) -> Option<(String, usize, bool)> {
        if bytes.is_empty() || bytes[0] != b'"' {
            return None;
        }
        let mut decoded = String::new();
        let mut i = 1;
        while i < bytes.len() {
            match bytes[i] {
                b'"' => {
                    return Some((decoded, i + 1, true));
                }
                b'\\' => {
                    i += 1;
                    if i >= bytes.len() {
                        return Some((decoded, i, false));
                    }
                    match bytes[i] {
                        b'"' => { decoded.push('"'); i += 1; }
                        b'\\' => { decoded.push('\\'); i += 1; }
                        b'/' => { decoded.push('/'); i += 1; }
                        b'b' => { decoded.push('\x08'); i += 1; }
                        b'f' => { decoded.push('\x0c'); i += 1; }
                        b'n' => { decoded.push('\n'); i += 1; }
                        b'r' => { decoded.push('\r'); i += 1; }
                        b't' => { decoded.push('\t'); i += 1; }
                        b'0' => { decoded.push('\0'); i += 1; }
                        b'a' => { decoded.push('\x07'); i += 1; }
                        b'e' => { decoded.push('\x1b'); i += 1; }
                        b'v' => { decoded.push('\x0b'); i += 1; }
                        b'\n' | b'\r' => {
                            if bytes[i] == b'\r' && bytes.get(i + 1) == Some(&b'\n') { i += 1; }
                            i += 1;
                            while i < bytes.len() && matches!(bytes[i], b' ' | b'\t') { i += 1; }
                        }
                        b'x' => {
                            i += 1;
                            if i + 2 > bytes.len() {
                                return Some((decoded, bytes.len(), false));
                            }
                            let hex_str = match std::str::from_utf8(&bytes[i..i + 2]) {
                                Ok(s) => s,
                                Err(_) => return Some((decoded, bytes.len(), false)),
                            };
                            let code = match u8::from_str_radix(hex_str, 16) {
                                Ok(c) => c,
                                Err(_) => return Some((decoded, bytes.len(), false)),
                            };
                            decoded.push(code as char);
                            i += 2;
                        }
                        b'u' => {
                            i += 1;
                            if i + 4 > bytes.len() {
                                return Some((decoded, bytes.len(), false));
                            }
                            let hex_str = match std::str::from_utf8(&bytes[i..i + 4]) {
                                Ok(s) => s,
                                Err(_) => return Some((decoded, bytes.len(), false)),
                            };
                            let code = match u16::from_str_radix(hex_str, 16) {
                                Ok(c) => c,
                                Err(_) => return Some((decoded, bytes.len(), false)),
                            };
                            i += 4;
                            if let Some(ch) = char::from_u32(code as u32) {
                                decoded.push(ch);
                            }
                        }
                        b'U' => {
                            i += 1;
                            if i + 8 > bytes.len() {
                                return Some((decoded, bytes.len(), false));
                            }
                            let hex_str = match std::str::from_utf8(&bytes[i..i + 8]) {
                                Ok(s) => s,
                                Err(_) => return Some((decoded, bytes.len(), false)),
                            };
                            let code = match u32::from_str_radix(hex_str, 16) {
                                Ok(c) => c,
                                Err(_) => return Some((decoded, bytes.len(), false)),
                            };
                            i += 8;
                            if let Some(ch) = char::from_u32(code) {
                                decoded.push(ch);
                            }
                        }
                        _ => {
                            decoded.push(bytes[i] as char);
                            i += 1;
                        }
                    }
                }
                b => {
                    if b < 128 {
                        decoded.push(b as char);
                        i += 1;
                    } else {
                        let s = match std::str::from_utf8(&bytes[i..]) {
                            Ok(s) => s,
                            Err(_) => return Some((decoded, bytes.len(), false)),
                        };
                        let ch = match s.chars().next() {
                            Some(c) => c,
                            None => return Some((decoded, bytes.len(), false)),
                        };
                        decoded.push(ch);
                        i += ch.len_utf8();
                    }
                }
            }
        }
        Some((decoded, i, false))
    }

    fn is_secret_prefix_candidate(s: &str) -> bool {
        const SECRET_PREFIXES: &[&str] = &[
            "ghp_",
            "github_pat_",
            "AKIA",
            "sk-proj-",
            "sk-",
            "sk_live_",
            "rk_live_",
            "xoxb-",
            "eyJhbGciOi",
        ];
        SECRET_PREFIXES.iter().any(|p| p.starts_with(s) && p.len() > s.len())
    }

    fn find_split_attachment(prev_recent: &str, working: &str) -> Option<usize> {
        const PW_KEYS: &[&str] = &[
            "password", "passwd", "pwd", "secret",
            "api_key", "token", "github_token", "aws_secret_access_key",
        ];
        const OTHER_KEYS: &[&str] = &[
            "contact ", "email=", "host=", "peer=", "bearer ", "token ",
        ];

        let max_split = prev_recent.len().min(1024);
        for split in (1..=max_split).rev() {
            let start_in_prev = prev_recent.len() - split;
            if !prev_recent.is_char_boundary(start_in_prev) {
                continue;
            }
            let cand = &prev_recent[start_in_prev..];
            let is_boundary = start_in_prev == 0 || {
                let prev_char = prev_recent[..start_in_prev].chars().last().unwrap();
                prev_char.is_whitespace() || prev_char == '{' || prev_char == '(' || prev_char == ';' || prev_char == ',' || prev_char == '"' || prev_char == '\''
            };
            if !is_boundary {
                continue;
            }

            let combined = format!("{}{}", cand, working);
            let comb_bytes = combined.as_bytes();

            // 1. Check URI scheme: [SCHEME]:// (e.g. ftp://, postgres://, etc.)
            if comb_bytes.len() >= 3 && comb_bytes[0].is_ascii_alphabetic() {
                let mut c = 1;
                while c < comb_bytes.len() && (comb_bytes[c].is_ascii_alphanumeric() || comb_bytes[c] == b'+' || comb_bytes[c] == b'-' || comb_bytes[c] == b'.') {
                    c += 1;
                }
                if c >= 1 && c < comb_bytes.len() && comb_bytes[c..].starts_with(b"://") {
                    let uri_prefix_len = c + 3;
                    if uri_prefix_len > split {
                        return Some(split);
                    }
                }
            }

            // 2. Check other simple keys
            for &k in OTHER_KEYS {
                let k_bytes = k.as_bytes();
                if comb_bytes.len() >= k_bytes.len() && comb_bytes[..k_bytes.len()].eq_ignore_ascii_case(k_bytes) {
                    if split < k_bytes.len() {
                        return Some(split);
                    }
                }
            }

            // 3. Check PW_KEYS: [{|(] + [spaces*] + [quote?] + [KEY] + [quote?] + [spaces*] + [=|:] + [spaces*]
            let mut cursor = 0;
            if cursor < comb_bytes.len() && (comb_bytes[cursor] == b'{' || comb_bytes[cursor] == b'(' || comb_bytes[cursor] == b'[' || comb_bytes[cursor] == b',') {
                cursor += 1;
            }
            while cursor < comb_bytes.len() && comb_bytes[cursor].is_ascii_whitespace() {
                cursor += 1;
            }

            // 3a. Check JSON-encoded key starting with '"'
            if cursor < comb_bytes.len() && comb_bytes[cursor] == b'"' {
                if let Some((decoded, bytes_consumed, is_closed)) = Self::decode_json_key_prefix(&comb_bytes[cursor..]) {
                    if is_closed {
                        if Self::is_sensitive_key(&decoded) {
                            let mut c = cursor + bytes_consumed;
                            while c < comb_bytes.len() && comb_bytes[c].is_ascii_whitespace() {
                                c += 1;
                            }
                            if c < comb_bytes.len() && (comb_bytes[c] == b'=' || comb_bytes[c] == b':') {
                                c += 1;
                                while c < comb_bytes.len() && comb_bytes[c].is_ascii_whitespace() {
                                    c += 1;
                                }
                                if c > split {
                                    return Some(split);
                                }
                            } else if c >= split && split < cursor + bytes_consumed {
                                return Some(split);
                            }
                        }
                    } else {
                        // Incomplete / unclosed key string
                        if !decoded.is_empty() && PW_KEYS.iter().any(|k| k.starts_with(&decoded.to_ascii_lowercase())) {
                            if split <= cursor + bytes_consumed {
                                return Some(split);
                            }
                        }
                    }
                }
            }

            let mut has_quote = false;
            if cursor < comb_bytes.len() && (comb_bytes[cursor] == b'"' || comb_bytes[cursor] == b'\'') {
                has_quote = true;
                cursor += 1;
            }

            for &key in PW_KEYS {
                let k_bytes = key.as_bytes();
                if cursor + k_bytes.len() <= comb_bytes.len() && comb_bytes[cursor..cursor + k_bytes.len()].eq_ignore_ascii_case(k_bytes) {
                    let mut c = cursor + k_bytes.len();
                    if has_quote {
                        if c < comb_bytes.len() && (comb_bytes[c] == b'"' || comb_bytes[c] == b'\'') {
                            c += 1;
                        } else if c >= comb_bytes.len() {
                            if split <= c {
                                return Some(split);
                            }
                        }
                    }
                    if has_quote {
                        while c < comb_bytes.len() && comb_bytes[c].is_ascii_whitespace() {
                            c += 1;
                        }
                    } else {
                        while c < comb_bytes.len() && (comb_bytes[c] == b' ' || comb_bytes[c] == b'\t') {
                            c += 1;
                        }
                    }
                    if c < comb_bytes.len() && (comb_bytes[c] == b'=' || comb_bytes[c] == b':') {
                        c += 1;
                        if has_quote {
                            while c < comb_bytes.len() && comb_bytes[c].is_ascii_whitespace() {
                                c += 1;
                            }
                        } else {
                            while c < comb_bytes.len() && (comb_bytes[c] == b' ' || comb_bytes[c] == b'\t') {
                                c += 1;
                            }
                        }
                        if c > split {
                            return Some(split);
                        }
                    } else if c >= split && split < cursor + k_bytes.len() {
                        return Some(split);
                    }
                }
            }

            // 4. Check secret token prefixes (e.g. g + hp_...)
            const TOKEN_PREFIXES: &[&str] = &[
                "ghp_", "github_pat_", "AKIA", "sk-proj-", "sk-", "sk_live_", "rk_live_", "xoxb-", "eyJhbGciOi",
            ];
            for &tp in TOKEN_PREFIXES {
                let tp_bytes = tp.as_bytes();
                if comb_bytes.len() >= tp_bytes.len() && comb_bytes[..tp_bytes.len()].starts_with(tp_bytes) {
                    if split < tp_bytes.len() {
                        return Some(split);
                    }
                }
            }
        }
        None
    }

    fn ends_with_pw_key_with_opt_yaml_props(text: &str) -> bool {
        let trimmed = text.trim_end_matches(|c| c == ' ' || c == '\t');
        let mut s = trimmed;
        while let Some(last_word_start) = s.rfind(|c: char| c.is_whitespace()) {
            let word = &s[last_word_start + 1..];
            if word.starts_with('!') || word.starts_with('&') {
                s = s[..last_word_start].trim_end_matches(|c| c == ' ' || c == '\t');
            } else {
                break;
            }
        }
        if s.starts_with('!') || s.starts_with('&') {
            return false;
        }
        Self::ends_with_pw_key(s)
    }

    fn get_pw_key_start(text: &str) -> usize {
        let trimmed = text.trim_end_matches(|c| c == ' ' || c == '\t');
        let mut s = trimmed;
        while let Some(last_word_start) = s.rfind(|c: char| c.is_whitespace()) {
            let word = &s[last_word_start + 1..];
            if word.starts_with('!') || word.starts_with('&') {
                s = s[..last_word_start].trim_end_matches(|c| c == ' ' || c == '\t');
            } else {
                break;
            }
        }
        let before_colon = s.trim_end_matches(|c| c == ' ' || c == '\t');
        let before_colon = if before_colon.ends_with(':') || before_colon.ends_with('=') {
            &before_colon[..before_colon.len() - 1]
        } else {
            before_colon
        };
        let before_colon = before_colon.trim_end_matches(|c| c == ' ' || c == '\t');
        before_colon
            .char_indices()
            .rfind(|&(_, c)| c.is_whitespace() || c == '{' || c == '(' || c == ';' || c == ',')
            .map(|(p, c)| p + c.len_utf8())
            .unwrap_or(0)
    }

    fn find_incomplete_yaml_header(text: &str) -> Option<usize> {
        let last_nl = text.rfind('\n').map(|p| p + 1).unwrap_or(0);
        let last_line = &text[last_nl..];
        let trimmed = last_line.trim_end_matches(|c| c == ' ' || c == '\t');
        let bytes = trimmed.as_bytes();

        let mut idx = 0;
        while idx < bytes.len() {
            if bytes[idx] == b'"' {
                if let Some((decoded, len)) = Self::decode_json_key(&bytes[idx..]) {
                    if Self::is_sensitive_key(&decoded) {
                        let key_start = idx;
                        let mut cursor = idx + len;
                        while cursor < bytes.len() && (bytes[cursor] == b' ' || bytes[cursor] == b'\t') {
                            cursor += 1;
                        }
                        if cursor < bytes.len() && bytes[cursor] == b':' {
                            cursor += 1;
                            while cursor < bytes.len() && (bytes[cursor] == b' ' || bytes[cursor] == b'\t') {
                                cursor += 1;
                            }
                            if cursor < bytes.len() && (bytes[cursor] == b'!' || bytes[cursor] == b'&' || bytes[cursor] == b'|' || bytes[cursor] == b'>') {
                                return Some(last_nl + key_start);
                            }
                        }
                    }
                }
            }
            idx += 1;
        }

        const PW_KEYS: &[&str] = &[
            "password", "passwd", "pwd", "secret",
            "api_key", "token", "github_token", "aws_secret_access_key",
        ];
        for &k in PW_KEYS {
            let k_bytes = k.as_bytes();
            let lower = trimmed.to_ascii_lowercase();
            if let Some(pos) = lower.find(k) {
                let key_start = if pos > 0 && (bytes[pos - 1] == b'"' || bytes[pos - 1] == b'\'') {
                    pos - 1
                } else {
                    pos
                };
                let mut cursor = pos + k_bytes.len();
                if cursor < bytes.len() && (bytes[cursor] == b'"' || bytes[cursor] == b'\'') {
                    cursor += 1;
                }
                while cursor < bytes.len() && (bytes[cursor] == b' ' || bytes[cursor] == b'\t') {
                    cursor += 1;
                }
                if cursor < bytes.len() && bytes[cursor] == b':' {
                    cursor += 1;
                    while cursor < bytes.len() && (bytes[cursor] == b' ' || bytes[cursor] == b'\t') {
                        cursor += 1;
                    }
                    if cursor < bytes.len() && (bytes[cursor] == b'!' || bytes[cursor] == b'&' || bytes[cursor] == b'|' || bytes[cursor] == b'>') {
                        return Some(last_nl + key_start);
                    }
                }
            }
        }
        None
    }

    fn find_uncompleted_quoted_key(text: &str) -> Option<usize> {
        let bytes = text.as_bytes();
        let mut idx = 0;
        while idx < bytes.len() {
            if bytes[idx] == b'"' {
                if let Some((decoded, len)) = Self::decode_json_key(&bytes[idx..]) {
                    if Self::is_sensitive_key(&decoded) {
                        let key_start = idx;
                        let mut cursor = idx + len;
                        while cursor < bytes.len() && bytes[cursor].is_ascii_whitespace() {
                            cursor += 1;
                        }
                        if cursor == bytes.len() {
                            return Some(key_start);
                        }
                        if cursor < bytes.len() && (bytes[cursor] == b':' || bytes[cursor] == b'=') {
                            cursor += 1;
                            while cursor < bytes.len() && bytes[cursor].is_ascii_whitespace() {
                                cursor += 1;
                            }
                            if cursor == bytes.len() {
                                return Some(key_start);
                            }
                        }
                    }
                }
            }
            idx += 1;
        }

        const PW_KEYS: &[&str] = &[
            "password", "passwd", "pwd", "secret",
            "api_key", "token", "github_token", "aws_secret_access_key",
        ];
        for &k in PW_KEYS {
            let k_bytes = k.as_bytes();
            let lower = text.to_ascii_lowercase();
            let mut search_idx = 0;
            while let Some(pos) = lower[search_idx..].find(k) {
                let abs_key = search_idx + pos;
                if abs_key > 0 && (bytes[abs_key - 1] == b'"' || bytes[abs_key - 1] == b'\'') {
                    let quote = bytes[abs_key - 1];
                    let key_start = abs_key - 1;
                    let mut cursor = abs_key + k_bytes.len();
                    if cursor < bytes.len() && bytes[cursor] == quote {
                        cursor += 1;
                        while cursor < bytes.len() && bytes[cursor].is_ascii_whitespace() {
                            cursor += 1;
                        }
                        if cursor == bytes.len() {
                            return Some(key_start);
                        }
                        if cursor < bytes.len() && (bytes[cursor] == b':' || bytes[cursor] == b'=') {
                            cursor += 1;
                            while cursor < bytes.len() && bytes[cursor].is_ascii_whitespace() {
                                cursor += 1;
                            }
                            if cursor == bytes.len() {
                                return Some(key_start);
                            }
                        }
                    }
                }
                search_idx = abs_key + k_bytes.len();
            }
        }
        None
    }

    fn ends_with_pw_key(text: &str) -> bool {
        let trimmed = text.trim_end_matches(|c| c == ' ' || c == '\t');
        if !trimmed.ends_with('=') && !trimmed.ends_with(':') {
            return false;
        }
        let before = trimmed[..trimmed.len() - 1].trim_end_matches(|c| c == ' ' || c == '\t');
        if before.len() >= 2 && before.starts_with('"') && before.ends_with('"') {
            if let Some((decoded, len)) = Self::decode_json_key(before.as_bytes()) {
                if len == before.len() && Self::is_sensitive_key(&decoded) {
                    return true;
                }
            }
        }
        let unquoted = if before.len() >= 2
            && ((before.ends_with('"') && before.starts_with('"'))
                || (before.ends_with('\'') && before.starts_with('\'')))
        {
            &before[1..before.len() - 1]
        } else if before.len() >= 2 && before.ends_with('"') {
            let pos = before[..before.len() - 1].rfind('"');
            if let Some(p) = pos {
                &before[p + 1..before.len() - 1]
            } else {
                ""
            }
        } else if before.len() >= 2 && before.ends_with('\'') {
            let pos = before[..before.len() - 1].rfind('\'');
            if let Some(p) = pos {
                &before[p + 1..before.len() - 1]
            } else {
                ""
            }
        } else {
            before
                .rsplit(|c: char| c.is_whitespace() || c == '{' || c == '(' || c == ';' || c == ',')
                .next()
                .unwrap_or("")
        };
        const PW_KEYS: &[&str] = &[
            "password", "passwd", "pwd", "secret",
            "api_key", "token", "github_token", "aws_secret_access_key",
        ];
        PW_KEYS.iter().any(|k| unquoted.eq_ignore_ascii_case(k))
    }

    fn find_unclosed_quoted_key(text: &str) -> Option<(usize, char)> {
        let bytes = text.as_bytes();
        let mut idx = 0;
        while idx < bytes.len() {
            if bytes[idx] == b'"' {
                if let Some((decoded, len)) = Self::decode_json_key(&bytes[idx..]) {
                    if Self::is_sensitive_key(&decoded) {
                        let key_start = idx;
                        let mut cursor = idx + len;
                        while cursor < bytes.len() && bytes[cursor].is_ascii_whitespace() {
                            cursor += 1;
                        }
                        if cursor < bytes.len() && (bytes[cursor] == b'=' || bytes[cursor] == b':') {
                            cursor += 1;
                            while cursor < bytes.len() && bytes[cursor].is_ascii_whitespace() {
                                cursor += 1;
                            }
                            if cursor < bytes.len() && (bytes[cursor] == b'"' || bytes[cursor] == b'\'') {
                                let quote = bytes[cursor] as char;
                                let val_after = &text[cursor + 1..];
                                let mut escaped = false;
                                let mut closed = false;
                                let mut i = 0;
                                let val_bytes = val_after.as_bytes();
                                while i < val_bytes.len() {
                                    if escaped {
                                        escaped = false;
                                        i += 1;
                                    } else if val_bytes[i] == b'\\' {
                                        escaped = true;
                                        i += 1;
                                    } else if val_bytes[i] as char == quote {
                                        if quote == '\'' && i + 1 < val_bytes.len() && val_bytes[i + 1] == b'\'' {
                                            i += 2;
                                        } else if quote == '\'' && i + 1 == val_bytes.len() {
                                            closed = false;
                                            break;
                                        } else {
                                            closed = true;
                                            break;
                                        }
                                    } else {
                                        i += 1;
                                    }
                                }
                                if escaped || !closed {
                                    return Some((key_start, quote));
                                }
                            }
                        }
                    }
                }
            }
            idx += 1;
        }

        const PW_KEYS: &[&str] = &[
            "password", "passwd", "pwd", "secret",
            "api_key", "token", "github_token", "aws_secret_access_key",
        ];
        let bytes = text.as_bytes();
        for &k in PW_KEYS {
            let k_bytes = k.as_bytes();
            let mut search_idx = 0;
            let lower = text.to_ascii_lowercase();
            while let Some(pos) = lower[search_idx..].find(k) {
                let abs_key = search_idx + pos;
                let key_start = if abs_key > 0 && (bytes[abs_key - 1] == b'"' || bytes[abs_key - 1] == b'\'') {
                    abs_key - 1
                } else {
                    abs_key
                };
                let is_quoted_key = key_start < abs_key;
                let mut cursor = abs_key + k_bytes.len();
                if cursor < bytes.len() && (bytes[cursor] == b'"' || bytes[cursor] == b'\'') {
                    cursor += 1;
                }
                if is_quoted_key {
                    while cursor < bytes.len() && bytes[cursor].is_ascii_whitespace() {
                        cursor += 1;
                    }
                } else {
                    while cursor < bytes.len() && (bytes[cursor] == b' ' || bytes[cursor] == b'\t') {
                        cursor += 1;
                    }
                }
                if cursor < bytes.len() && (bytes[cursor] == b'=' || bytes[cursor] == b':') {
                    cursor += 1;
                    if is_quoted_key {
                        while cursor < bytes.len() && bytes[cursor].is_ascii_whitespace() {
                            cursor += 1;
                        }
                    } else {
                        while cursor < bytes.len() && (bytes[cursor] == b' ' || bytes[cursor] == b'\t') {
                            cursor += 1;
                        }
                    }
                    if cursor < bytes.len() && (bytes[cursor] == b'"' || bytes[cursor] == b'\'') {
                        let quote = bytes[cursor] as char;
                        let val_after = &text[cursor + 1..];
                        let mut escaped = false;
                        let mut closed = false;
                        let mut i = 0;
                        let val_bytes = val_after.as_bytes();
                        while i < val_bytes.len() {
                            if escaped {
                                escaped = false;
                                i += 1;
                            } else if val_bytes[i] == b'\\' {
                                escaped = true;
                                i += 1;
                            } else if val_bytes[i] as char == quote {
                                if quote == '\'' && i + 1 < val_bytes.len() && val_bytes[i + 1] == b'\'' {
                                    i += 2;
                                } else if quote == '\'' && i + 1 == val_bytes.len() {
                                    closed = false;
                                    break;
                                } else {
                                    closed = true;
                                    break;
                                }
                            } else {
                                i += 1;
                            }
                        }
                        if escaped || !closed {
                            return Some((key_start, quote));
                        }
                    }
                }
                search_idx = abs_key + k_bytes.len();
            }
        }
        None
    }

    fn split_stream_chunk<'a>(&self, text: &'a str, in_yaml_block: bool) -> (&'a str, &'a str, Option<AwaitingPasswordState>, bool, bool, bool, bool) {
        if text.is_empty() {
            return ("", "", None, false, false, false, false);
        }

        // 1. Incomplete or unclosed Private Key block: withhold from the begin tag until closing dashes
        if let Some(begin_pos) = text.rfind("-----BEGIN ") {
            let header = &text[begin_pos..];
            let first_line = header.lines().next().unwrap_or("");
            if !header.contains('\n') {
                return (&text[..begin_pos], &text[begin_pos..], None, false, false, false, false);
            }
            if first_line.contains("PRIVATE KEY") || first_line.contains("RSA PRIVATE") || first_line.contains("OPENSSH PRIVATE") {
                let is_closed = if let Some(p) = header.find("-----END ") {
                    header[p + 9..].find("-----").is_some()
                } else {
                    false
                };
                if !is_closed {
                    return (&text[..begin_pos], &text[begin_pos..], None, false, false, false, false);
                }
            }
        }

        // Check if chunk ends in unclosed quote after an assignment key (e.g. password="Alpha or 'password': "Alpha)
        if let Some((key_start, _)) = Self::find_unclosed_quoted_key(text) {
            return (&text[..key_start], &text[key_start..], None, false, false, false, false);
        }

        // If chunk ends in an incomplete YAML block indicator after a pw key (e.g. "password: |" without newline):
        if let Some(pipe_pos) = text.rfind(|c| c == '|' || c == '>') {
            let after = &text[pipe_pos + 1..];
            if !after.contains('\n') && !after.contains('\r') {
                let before = text[..pipe_pos].trim_end_matches(|c| c == ' ' || c == '\t');
                if Self::ends_with_pw_key_with_opt_yaml_props(before) {
                    let key_start = Self::get_pw_key_start(before);
                    return (&text[..key_start], &text[key_start..], None, false, false, false, false);
                }
            }
        }

        // Incomplete YAML header on the last line (e.g. "password: !!str" or "password: &cred" without newline)
        if let Some(key_start) = Self::find_incomplete_yaml_header(text) {
            return (&text[..key_start], &text[key_start..], None, false, false, false, false);
        }

        // Incomplete JSON quoted key waiting for separator or value (e.g. `{"password"` or `{"password":\n`)
        if let Some(key_start) = Self::find_uncompleted_quoted_key(text) {
            return (&text[..key_start], &text[key_start..], None, false, false, false, false);
        }

        // Incomplete unquoted or quoted password key on last line awaiting assignment / value (e.g. "password   ")
        if !text.ends_with('\n') {
            let last_nl = text.rfind('\n').map(|p| p + 1).unwrap_or(0);
            let last_line = &text[last_nl..];
            let trimmed_end = last_line.trim_end_matches(|c| c == ' ' || c == '\t' || c == '\r');
            if last_line.len() > trimmed_end.len() && !trimmed_end.is_empty() && !trimmed_end.ends_with(':') && !trimmed_end.ends_with('=') {
                let last_word_start = trimmed_end
                    .char_indices()
                    .rfind(|&(_, c)| c.is_whitespace() || c == '{' || c == '(' || c == ';' || c == ',')
                    .map(|(p, c)| p + c.len_utf8())
                    .unwrap_or(0);
                let word = &trimmed_end[last_word_start..];
                let is_pw = if word.starts_with('"') && word.ends_with('"') && word.len() >= 2 {
                    if let Some((decoded, len)) = Self::decode_json_key(word.as_bytes()) {
                        len == word.len() && Self::is_sensitive_key(&decoded)
                    } else {
                        false
                    }
                } else {
                    let unquoted = if (word.starts_with('"') && word.ends_with('"')) || (word.starts_with('\'') && word.ends_with('\'')) {
                        if word.len() >= 2 { &word[1..word.len() - 1] } else { "" }
                    } else {
                        word
                    };
                    const PW_KEYS: &[&str] = &[
                        "password", "passwd", "pwd", "secret",
                        "api_key", "token", "github_token", "aws_secret_access_key",
                    ];
                    PW_KEYS.iter().any(|k| unquoted.eq_ignore_ascii_case(k))
                };
                if is_pw {
                    let key_start = last_nl + last_word_start;
                    return (&text[..key_start], &text[key_start..], None, false, false, false, false);
                }
            }
        }

        // If inside a YAML block or chunk starts a YAML block with incomplete body line:
        let is_yaml_candidate = in_yaml_block || {
            if let Some(hdr_pos) = text.rfind(|c| c == '|' || c == '>') {
                let after = &text[hdr_pos + 1..];
                if after.contains('\n') {
                    let before = text[..hdr_pos].trim_end_matches(|c| c == ' ' || c == '\t');
                    Self::ends_with_pw_key_with_opt_yaml_props(before)
                } else {
                    false
                }
            } else if let Some(last_nl) = text.rfind('\n') {
                let before = text[..last_nl].trim_end_matches(|c| c == ' ' || c == '\t');
                let last_non_comment = before.lines().rev().find(|l| {
                    let tr = l.trim_start_matches(|c| c == ' ' || c == '\t');
                    !tr.is_empty() && !tr.starts_with('#')
                });
                if let Some(before_line) = last_non_comment {
                    let clean_line = if let Some(hash_pos) = before_line.find('#') {
                        before_line[..hash_pos].trim_end_matches(|c| c == ' ' || c == '\t')
                    } else {
                        before_line.trim_end_matches(|c| c == ' ' || c == '\t')
                    };
                    Self::ends_with_pw_key_with_opt_yaml_props(clean_line)
                } else {
                    false
                }
            } else {
                false
            }
        };

        if is_yaml_candidate && !text.ends_with('\n') {
            if let Some(pos) = text.rfind('\n') {
                return (&text[..=pos], &text[pos + 1..], None, false, false, false, false);
            } else {
                return ("", text, None, false, false, false, false);
            }
        }

        // Complete line ending in newline: complete line
        if text.ends_with('\n') {
            return (text, "", None, false, false, false, false);
        }

        // Incomplete PEM prefix at end of chunk: "-----", "-----BEGIN"
        let pem_prefix = "-----BEGIN ";
        for len in 1..=pem_prefix.len() {
            let cand = &pem_prefix[..len];
            if text.ends_with(cand) {
                let cand_start = text.len() - len;
                if cand_start == 0 || text[..cand_start].ends_with('\n') {
                    return (&text[..cand_start], &text[cand_start..], None, false, false, false, false);
                }
            }
        }

        // Unclosed URI authority / credentials (e.g. postgres://u: or postgres://u:AlphaSecret...)
        if let Some(scheme_pos) = text.rfind("://") {
            let tail = &text[scheme_pos + 3..];
            if !tail.contains('\n') && !tail.contains('\r') && !tail.contains(' ') && !tail.contains('/') {
                if !tail.contains('@') {
                    let scheme_start = text[..scheme_pos]
                        .char_indices()
                        .rfind(|&(_, c)| !c.is_ascii_alphanumeric() && c != '+' && c != '-' && c != '.')
                        .map(|(p, c)| p + c.len_utf8())
                        .unwrap_or(0);
                    return (&text[..scheme_start], &text[scheme_start..], None, false, false, false, false);
                }
            }
        }

        // Partial URI scheme before "://" (e.g. "postgres:", "ftp:", or "postgres:/")
        for colon_cand in &[":/", ":"] {
            if text.ends_with(colon_cand) {
                let before_colon = &text[..text.len() - colon_cand.len()];
                if !before_colon.contains("://") {
                    let scheme_start = before_colon
                        .char_indices()
                        .rfind(|&(_, c)| !c.is_ascii_alphanumeric() && c != '+' && c != '-' && c != '.')
                        .map(|(p, c)| p + c.len_utf8())
                        .unwrap_or(0);
                    let prev_char = if scheme_start > 0 { before_colon[..scheme_start].chars().last() } else { None };
                    if prev_char != Some(':') {
                        let scheme = &before_colon[scheme_start..];
                        if scheme.len() >= 1 && scheme.chars().next().map(|c| c.is_ascii_alphabetic()).unwrap_or(false) {
                            return (&text[..scheme_start], &text[scheme_start..], None, false, false, false, false);
                        }
                    }
                }
            }
        }

        // Check if chunk ends with quote opened after secret key:
        if text.ends_with("password=\"") || text.ends_with("secret=\"") {
            return (text, "", None, false, false, true, false);
        }
        if text.ends_with("password='") || text.ends_with("secret='") {
            return (text, "", None, false, false, false, true);
        }

        // Check if chunk ends exactly with an assignment key awaiting value:
        if Self::ends_with_pw_key(text) {
            let trimmed = text.trim_end_matches(|c| c == ' ' || c == '\t');
            let is_env = trimmed.ends_with('=');
            let before = trimmed[..trimmed.len() - 1].trim_end_matches(|c| c == ' ' || c == '\t');
            let key_start = before
                .char_indices()
                .rfind(|&(_, c)| c.is_whitespace() || c == '{' || c == '(' || c == ';' || c == ',')
                .map(|(p, c)| p + c.len_utf8())
                .unwrap_or(0);
            let key_line_start = text[..key_start].rfind('\n').map(|p| p + 1).unwrap_or(0);
            let parent_indent = key_start - key_line_start;
            return (text, "", Some(AwaitingPasswordState { parent_indent, is_env }), false, false, false, false);
        }

        if text.ends_with("contact ") {
            let start = text.len() - 8;
            return (&text[..start], &text[start..], None, false, false, false, false);
        }
        if text.ends_with("email=") {
            let start = text.len() - 6;
            return (&text[..start], &text[start..], None, false, false, false, false);
        }
        if text.ends_with("host=") || text.ends_with("peer=") {
            let start = text.len() - 5;
            return (&text[..start], &text[start..], None, false, false, false, false);
        }

        // Check trailing partial value after key= or key: or /
        let key_prefixes = [
            ("host=", true),
            ("peer=", true),
            ("email=", false),
            ("contact ", false),
        ];
        for &(kp, is_host) in &key_prefixes {
            if let Some(idx) = text.rfind(kp) {
                let tail = &text[idx + kp.len()..];
                if !tail.contains('\n') && !tail.is_empty() {
                    let is_incomplete = if is_host {
                        if tail.parse::<Ipv4Addr>().is_ok() {
                            false
                        } else if tail.parse::<Ipv6Addr>().is_ok() {
                            tail.ends_with(':')
                        } else {
                            tail.contains('.') || tail.contains(':') || tail.chars().all(|c| c.is_ascii_hexdigit())
                        }
                    } else {
                        // email
                        if let Some(at_idx) = tail.find('@') {
                            let after_at = &tail[at_idx + 1..];
                            if let Some(dot_idx) = after_at.rfind('.') {
                                after_at[dot_idx + 1..].len() < 3
                            } else {
                                true
                            }
                        } else {
                            true
                        }
                    };
                    if is_incomplete {
                        return (&text[..idx], &text[idx..], None, false, false, false, false);
                    }
                }
            }
        }

        // Standalone partial token prefix candidate (length >= 2, or length >= 1 at start/after boundary)
        let last_word_start = text
            .char_indices()
            .rfind(|&(_, c)| {
                c.is_whitespace()
                    || c == '='
                    || c == ':'
                    || c == '"'
                    || c == '\''
                    || c == '`'
                    || c == ';'
                    || c == ','
                    || c == '{'
                    || c == '('
                    || c == '['
            })
            .map(|(p, c)| p + c.len_utf8())
            .unwrap_or(0);
        let trailing = &text[last_word_start..];
        if !trailing.is_empty() && Self::is_secret_prefix_candidate(trailing) {
            let before_delim = text[..last_word_start].trim_end_matches(|c| c == ' ' || c == '\t');
            if let Some(key_start) = Self::find_uncompleted_quoted_key(before_delim) {
                return (&text[..key_start], &text[key_start..], None, false, false, false, false);
            }
            if Self::ends_with_pw_key(before_delim) {
                let key_start = Self::get_pw_key_start(before_delim);
                return (&text[..key_start], &text[key_start..], None, false, false, false, false);
            }
            return (&text[..last_word_start], trailing, None, false, false, false, false);
        }

        (text, "", None, false, false, false, false)
    }

    #[allow(clippy::too_many_arguments)]
    fn extract_sensitive_assignment_value(
        text: &str,
        text_bytes: &[u8],
        key_start: usize,
        mut cursor: usize,
        sep: u8,
        internal_spans: &mut Vec<InternalSpan>,
        max_risk: &mut f32,
        active_yaml_block: &mut Option<YamlBlockState>,
        json_secret: &mut Option<JsonSecretState>,
    ) -> Option<usize> {
        // An enclosing JSON container already covers any assignments within it.
        if let Some(span) = internal_spans.iter().find(|s| {
            s.original_sample == "[REDACTED_JSON_VALUE]" && s.start <= key_start && key_start < s.end
        }) {
            return Some(span.end);
        }
        let key_line_start = text[..key_start].rfind('\n').map(|p| p + 1).unwrap_or(0);
        let parent_indent = key_start - key_line_start;

        let is_json_context = sep == b':' && text_bytes[key_start] == b'"' && {
            let before_key = text[..key_start].trim_end();
            before_key.ends_with('{') || before_key.ends_with(',')
        };
        if is_json_context && cursor < text_bytes.len() && text_bytes[cursor] != b'"' {
            let mut state = JsonSecretState::new(text_bytes[cursor]);
            let (length, closed) = state.consume(&text_bytes[cursor..]);
            let end = cursor + length;
            if length > 0 {
                internal_spans.push(InternalSpan {
                    category: "SECRET".to_string(),
                    start: cursor,
                    end,
                    original_sample: "[REDACTED_JSON_VALUE]".to_string(),
                    replacement: "\"[REDACTED_SECRET]\"".to_string(),
                });
                *max_risk = max_risk.max(0.9);
                if !closed {
                    *json_secret = Some(state);
                }
                return Some(end);
            }
        }

        if sep == b'=' {
            let is_json_context = text_bytes[key_start] == b'"' && {
                let before_key = text[..key_start].trim_end();
                before_key.ends_with('{') || before_key.ends_with(',')
            };

            let (val_start, val_end) = if cursor < text_bytes.len() && (text_bytes[cursor] == b'"' || text_bytes[cursor] == b'\'') {
                let quote = text_bytes[cursor];
                let v_start = cursor + 1;
                let mut v_end = v_start;
                while v_end < text_bytes.len() {
                    if text_bytes[v_end] == b'\\' && v_end + 1 < text_bytes.len() {
                        v_end += 2;
                        continue;
                    }
                    if quote == b'\'' && text_bytes[v_end] == b'\'' && v_end + 1 < text_bytes.len() && text_bytes[v_end + 1] == b'\'' {
                        v_end += 2;
                        continue;
                    }
                    if text_bytes[v_end] == quote {
                        break;
                    }
                    v_end += 1;
                }
                (v_start, v_end)
            } else if cursor < text_bytes.len() {
                let v_start = cursor;
                let mut v_end = v_start;
                while v_end < text_bytes.len() {
                    let b = text_bytes[v_end];
                    if is_json_context && (b == b',' || b == b'}' || b == b']' || b == b'\n' || b == b'\r') {
                        break;
                    } else if !is_json_context && (b == b'\n' || b == b'\r') {
                        break;
                    }
                    v_end += 1;
                }
                while is_json_context && v_end > v_start && text_bytes[v_end - 1].is_ascii_whitespace() {
                    v_end -= 1;
                }
                (v_start, v_end)
            } else {
                (0, 0)
            };

            if val_end > val_start {
                let replacement = if is_json_context && (cursor >= text_bytes.len() || (text_bytes[cursor] != b'"' && text_bytes[cursor] != b'\'')) {
                    "\"[REDACTED_SECRET]\"".to_string()
                } else {
                    "[REDACTED_SECRET]".to_string()
                };
                internal_spans.push(InternalSpan {
                    category: "SECRET".to_string(),
                    start: val_start,
                    end: val_end,
                    original_sample: "[REDACTED_PASSWORD]".to_string(),
                    replacement,
                });
                *max_risk = max_risk.max(0.9);
                return Some(val_end);
            }
        } else if sep == b':' {
            let mut prop_cursor = cursor;
            let mut has_props = false;
            while prop_cursor < text_bytes.len() && (text_bytes[prop_cursor] == b'!' || text_bytes[prop_cursor] == b'&') {
                has_props = true;
                while prop_cursor < text_bytes.len() && !text_bytes[prop_cursor].is_ascii_whitespace() {
                    prop_cursor += 1;
                }
                while prop_cursor < text_bytes.len() && (text_bytes[prop_cursor] == b' ' || text_bytes[prop_cursor] == b'\t') {
                    prop_cursor += 1;
                }
            }

            let is_yaml_block = if prop_cursor < text_bytes.len() && (text_bytes[prop_cursor] == b'|' || text_bytes[prop_cursor] == b'>') {
                let mut c = prop_cursor + 1;
                while c < text_bytes.len() && (text_bytes[c] == b'-' || text_bytes[c] == b'+' || text_bytes[c].is_ascii_digit()) {
                    c += 1;
                }
                while c < text_bytes.len() && (text_bytes[c] == b' ' || text_bytes[c] == b'\t') {
                    c += 1;
                }
                if c < text_bytes.len() && text_bytes[c] == b'#' {
                    while c < text_bytes.len() && text_bytes[c] != b'\r' && text_bytes[c] != b'\n' {
                        c += 1;
                    }
                }
                c == text_bytes.len() || text_bytes[c] == b'\n' || text_bytes[c] == b'\r'
            } else {
                false
            };

            let mut c = if is_yaml_block { prop_cursor + 1 } else { prop_cursor };
            let mut explicit_indent = None;
            if is_yaml_block {
                while c < text_bytes.len() && (text_bytes[c] == b'-' || text_bytes[c] == b'+' || text_bytes[c].is_ascii_digit()) {
                    if text_bytes[c] >= b'1' && text_bytes[c] <= b'9' && explicit_indent.is_none() {
                        explicit_indent = Some((text_bytes[c] - b'0') as usize);
                    }
                    c += 1;
                }
            }
            while c < text_bytes.len() && (text_bytes[c] == b' ' || text_bytes[c] == b'\t') {
                c += 1;
            }
            if c < text_bytes.len() && text_bytes[c] == b'#' {
                while c < text_bytes.len() && text_bytes[c] != b'\r' && text_bytes[c] != b'\n' {
                    c += 1;
                }
            }
            let is_line_end = c == text_bytes.len() || text_bytes[c] == b'\n' || text_bytes[c] == b'\r';

            let body_start = if c < text_bytes.len() && text_bytes[c] == b'\r' && c + 1 < text_bytes.len() && text_bytes[c + 1] == b'\n' {
                c + 2
            } else if c < text_bytes.len() && (text_bytes[c] == b'\n' || text_bytes[c] == b'\r') {
                c + 1
            } else {
                text_bytes.len()
            };

            let has_indented_following_line = if is_line_end && body_start < text_bytes.len() {
                let rest = &text[body_start..];
                let mut found = false;
                for line in rest.lines() {
                    let trimmed = line.trim_start_matches(|ch| ch == ' ' || ch == '\t');
                    if !trimmed.is_empty() {
                        if !is_yaml_block && trimmed.starts_with('#') {
                            continue;
                        }
                        let indent = line.len() - trimmed.len();
                        found = indent > parent_indent;
                        break;
                    }
                }
                found
            } else {
                false
            };

            if is_yaml_block || has_indented_following_line {
                let mut line_pos = body_start;
                let mut block_indent = explicit_indent.map(|n| parent_indent + n);
                let mut block_closed = false;

                while line_pos < text.len() {
                    let next_nl = text[line_pos..].find('\n').map(|p| line_pos + p);
                    let line_end = next_nl.unwrap_or(text.len());
                    let line = &text[line_pos..line_end].trim_end_matches('\r');
                    let trimmed = line.trim_start_matches(|ch| ch == ' ' || ch == '\t');

                    if trimmed.is_empty() || (!is_yaml_block && block_indent.is_none() && trimmed.starts_with('#')) {
                        if next_nl.is_none() {
                            break;
                        }
                        line_pos = next_nl.unwrap() + 1;
                        continue;
                    }

                    let indent = line.len() - trimmed.len();
                    if block_indent.is_none() {
                        if indent > parent_indent {
                            block_indent = Some(indent);
                        } else {
                            block_closed = true;
                            break;
                        }
                    }

                    if let Some(b_indent) = block_indent {
                        if indent < b_indent {
                            block_closed = true;
                            break;
                        }
                    }

                    let val_s = line_pos + indent;
                    let val_e = line_pos + line.len();
                    if val_e > val_s {
                        internal_spans.push(InternalSpan {
                            category: "SECRET".to_string(),
                            start: val_s,
                            end: val_e,
                            original_sample: "[REDACTED_PASSWORD]".to_string(),
                            replacement: "[REDACTED_SECRET]".to_string(),
                        });
                        *max_risk = max_risk.max(0.9);
                    }

                    if next_nl.is_none() {
                        line_pos = text.len();
                        break;
                    }
                    line_pos = next_nl.unwrap() + 1;
                }

                if !block_closed {
                    *active_yaml_block = Some(YamlBlockState {
                        parent_indent,
                        block_indent,
                        is_block_scalar: is_yaml_block,
                    });
                }
                return Some(line_pos);
            } else if is_line_end {
                let rest = if body_start < text_bytes.len() { &text[body_start..] } else { "" };
                let only_comments_or_empty = if is_yaml_block {
                    rest.lines().all(|l| l.trim_start_matches(|ch| ch == ' ' || ch == '\t').is_empty())
                } else {
                    rest.lines().all(|l| {
                        let tr = l.trim_start_matches(|ch| ch == ' ' || ch == '\t');
                        tr.is_empty() || tr.starts_with('#')
                    })
                };
                if body_start == text_bytes.len() || only_comments_or_empty {
                    *active_yaml_block = Some(YamlBlockState {
                        parent_indent,
                        block_indent: explicit_indent.map(|n| parent_indent + n),
                        is_block_scalar: is_yaml_block,
                    });
                    return Some(text_bytes.len());
                }
            }

            let has_inline_content = prop_cursor < text_bytes.len() && text_bytes[prop_cursor] != b'\r' && text_bytes[prop_cursor] != b'\n' && text_bytes[prop_cursor] != b'#';
            if has_props && has_inline_content {
                cursor = prop_cursor;
            }

            let is_json_context = text_bytes[key_start] == b'"' && {
                let before_key = text[..key_start].trim_end();
                before_key.ends_with('{') || before_key.ends_with(',')
            };

            let (val_start, val_end) = if cursor < text_bytes.len() && (text_bytes[cursor] == b'"' || text_bytes[cursor] == b'\'') {
                let quote = text_bytes[cursor];
                let v_start = cursor + 1;
                let mut v_end = v_start;
                while v_end < text_bytes.len() {
                    if text_bytes[v_end] == b'\\' && v_end + 1 < text_bytes.len() {
                        v_end += 2;
                        continue;
                    }
                    if quote == b'\'' && text_bytes[v_end] == b'\'' && v_end + 1 < text_bytes.len() && text_bytes[v_end + 1] == b'\'' {
                        v_end += 2;
                        continue;
                    }
                    if text_bytes[v_end] == quote {
                        break;
                    }
                    v_end += 1;
                }
                (v_start, v_end)
            } else if cursor < text_bytes.len() {
                let v_start = cursor;
                let mut v_end = v_start;
                while v_end < text_bytes.len() {
                    let b = text_bytes[v_end];
                    if is_json_context && (b == b',' || b == b'}' || b == b']' || b == b'\n' || b == b'\r') {
                        break;
                    } else if !is_json_context && (b == b'\n' || b == b'\r') {
                        break;
                    }
                    v_end += 1;
                }
                while is_json_context && v_end > v_start && text_bytes[v_end - 1].is_ascii_whitespace() {
                    v_end -= 1;
                }
                (v_start, v_end)
            } else {
                (0, 0)
            };

            if val_end > val_start {
                let replacement = if is_json_context && (cursor >= text_bytes.len() || (text_bytes[cursor] != b'"' && text_bytes[cursor] != b'\'')) {
                    "\"[REDACTED_SECRET]\"".to_string()
                } else {
                    "[REDACTED_SECRET]".to_string()
                };
                internal_spans.push(InternalSpan {
                    category: "SECRET".to_string(),
                    start: val_start,
                    end: val_end,
                    original_sample: "[REDACTED_PASSWORD]".to_string(),
                    replacement,
                });
                *max_risk = max_risk.max(0.9);
                return Some(val_end);
            }
        }
        None
    }

    fn scan_and_redact(
        &self,
        text: &str,
        initial_yaml_block: Option<YamlBlockState>,
    ) -> (String, Vec<RedactedSpan>, f32, bool, bool, Option<YamlBlockState>, bool, bool, bool, Option<JsonSecretState>) {
        let mut internal_spans: Vec<InternalSpan> = Vec::new();
        let mut max_risk = 0.0f32;
        let mut ended_in_pem = false;
        let mut text_scan_start = 0;
        let mut active_yaml_block = None;
        let mut json_secret = None;

        if let Some(mut yb) = initial_yaml_block {
            let mut line_pos = 0;
            let mut block_ended = false;

            while line_pos < text.len() {
                let next_nl = text[line_pos..].find('\n').map(|p| line_pos + p);
                let line_end = next_nl.unwrap_or(text.len());
                let line = &text[line_pos..line_end].trim_end_matches('\r');
                let trimmed = line.trim_start_matches(|ch| ch == ' ' || ch == '\t');

                if trimmed.is_empty() || (!yb.is_block_scalar && yb.block_indent.is_none() && trimmed.starts_with('#')) {
                    if next_nl.is_none() {
                        line_pos = text.len();
                        break;
                    }
                    line_pos = next_nl.unwrap() + 1;
                    continue;
                }

                let indent = line.len() - trimmed.len();
                if yb.block_indent.is_none() {
                    if indent > yb.parent_indent {
                        yb.block_indent = Some(indent);
                    } else {
                        block_ended = true;
                        break;
                    }
                }

                if let Some(b_indent) = yb.block_indent {
                    if indent < b_indent {
                        block_ended = true;
                        break;
                    }
                }

                let val_s = line_pos + indent;
                let val_e = line_pos + line.len();
                if val_e > val_s {
                    internal_spans.push(InternalSpan {
                        category: "SECRET".to_string(),
                        start: val_s,
                        end: val_e,
                        original_sample: "[REDACTED_PASSWORD]".to_string(),
                        replacement: "[REDACTED_SECRET]".to_string(),
                    });
                    max_risk = max_risk.max(0.9);
                }

                if next_nl.is_none() {
                    line_pos = text.len();
                    break;
                }
                line_pos = next_nl.unwrap() + 1;
            }

            if !block_ended {
                active_yaml_block = Some(yb);
            }
            text_scan_start = line_pos;
        }

        // 1. Private Key blocks (multi-line) — ONLY PRIVATE KEYS, NOT CERTIFICATES
        let mut search_idx = 0;
        while let Some(begin_pos) = text[search_idx..].find("-----BEGIN ") {
            let abs_begin = search_idx + begin_pos;
            let after_begin = &text[abs_begin..];
            let end_line = after_begin.find('\n').unwrap_or(after_begin.len());
            let header_line = &after_begin[..end_line];

            if header_line.contains("PRIVATE KEY") || header_line.contains("RSA PRIVATE") || header_line.contains("OPENSSH PRIVATE") {
                let end_tag = "-----END ";
                let end_pos = if let Some(p) = text[abs_begin..].find(end_tag) {
                    let abs_end_tag = abs_begin + p;
                    if let Some(dashes) = text[abs_end_tag + 9..].find("-----") {
                        let tag_end = abs_end_tag + 9 + dashes + 5;
                        if text[tag_end..].starts_with("\r\n") {
                            tag_end + 2
                        } else if text[tag_end..].starts_with('\n') {
                            tag_end + 1
                        } else {
                            if tag_end == text.len() {
                                ended_in_pem = true;
                            }
                            tag_end
                        }
                    } else {
                        text.len()
                    }
                } else {
                    text.len()
                };

                internal_spans.push(InternalSpan {
                    category: "SECRET_KEY".to_string(),
                    start: abs_begin,
                    end: end_pos,
                    original_sample: "[REDACTED_KEY]".to_string(),
                    replacement: "[REDACTED_SECRET]".to_string(),
                });
                max_risk = max_risk.max(1.0);
                search_idx = end_pos;
            } else {
                search_idx = abs_begin + 11;
            }
        }

        // 2. Known high-entropy secret prefixes (standalone)
        let secret_prefixes = [
            "ghp_",
            "github_pat_",
            "AKIA",
            "sk-proj-",
            "sk-",
            "sk_live_",
            "rk_live_",
            "xoxb-",
            "eyJhbGciOi",
        ];

        for prefix in &secret_prefixes {
            let mut s_idx = 0;
            while let Some(pos) = text[s_idx..].find(prefix) {
                let abs_pos = s_idx + pos;
                let token_end = text[abs_pos..]
                    .find(|c: char| c.is_whitespace() || c == '\'' || c == '"' || c == '`' || c == ';' || c == ',' || c == '}' || c == ')' || c == ']')
                    .map(|end| abs_pos + end)
                    .unwrap_or(text.len());

                let secret_val = &text[abs_pos..token_end];
                if secret_val.len() >= prefix.len() + 6 || (text.len() == token_end && secret_val.len() >= prefix.len()) {
                    internal_spans.push(InternalSpan {
                        category: "SECRET".to_string(),
                        start: abs_pos,
                        end: token_end,
                        original_sample: "[REDACTED_SECRET]".to_string(),
                        replacement: "[REDACTED_SECRET]".to_string(),
                    });
                    max_risk = max_risk.max(1.0);
                    s_idx = token_end;
                } else {
                    s_idx = abs_pos + prefix.len();
                }
            }
        }

        // 3. Password and sensitive field assignments (JSON, YAML, shell, env)
        let text_bytes = text.as_bytes();

        // 3a. Escaped / JSON-encoded sensitive keys: {"pass\u0077ord": "...", ...}
        let mut json_idx = text_scan_start;
        while json_idx < text_bytes.len() {
            if text_bytes[json_idx] == b'"' {
                if let Some((decoded, key_len)) = Self::decode_json_key(&text_bytes[json_idx..]) {
                    if Self::is_sensitive_key(&decoded) {
                        let key_start = json_idx;
                        let mut cursor = json_idx + key_len;
                        while cursor < text_bytes.len() && text_bytes[cursor].is_ascii_whitespace() {
                            cursor += 1;
                        }
                        if cursor < text_bytes.len() && (text_bytes[cursor] == b'=' || text_bytes[cursor] == b':') {
                            let sep = text_bytes[cursor];
                            cursor += 1;
                            while cursor < text_bytes.len() && text_bytes[cursor].is_ascii_whitespace() {
                                cursor += 1;
                            }
                            if let Some(next_pos) = Self::extract_sensitive_assignment_value(
                                text,
                                text_bytes,
                                key_start,
                                cursor,
                                sep,
                                &mut internal_spans,
                                &mut max_risk,
                                &mut active_yaml_block,
                                &mut json_secret,
                            ) {
                                json_idx = next_pos;
                                continue;
                            }
                        }
                    }
                }
            }
            json_idx += 1;
        }

        // 3b. Password and sensitive field assignments (YAML, shell, env, plain)
        let pw_keys = [
            "password", "passwd", "pwd", "secret",
            "github_token", "api_key", "token", "aws_secret_access_key",
        ];

        for key in &pw_keys {
            let k_bytes = key.as_bytes();
            let mut i = text_scan_start;
            while i + k_bytes.len() <= text_bytes.len() {
                if text_bytes[i..i + k_bytes.len()].eq_ignore_ascii_case(k_bytes) {
                    let key_start = if i > 0 && (text_bytes[i - 1] == b'"' || text_bytes[i - 1] == b'\'') {
                        i - 1
                    } else {
                        i
                    };
                    let is_quoted_key = key_start < i;
                    let mut cursor = i + k_bytes.len();
                    if cursor < text_bytes.len() && (text_bytes[cursor] == b'"' || text_bytes[cursor] == b'\'') {
                        cursor += 1;
                    }
                    if is_quoted_key {
                        while cursor < text_bytes.len() && text_bytes[cursor].is_ascii_whitespace() {
                            cursor += 1;
                        }
                    } else {
                        while cursor < text_bytes.len() && (text_bytes[cursor] == b' ' || text_bytes[cursor] == b'\t') {
                            cursor += 1;
                        }
                    }
                    if cursor < text_bytes.len() && (text_bytes[cursor] == b'=' || text_bytes[cursor] == b':') {
                        let sep = text_bytes[cursor];
                        cursor += 1;
                        if is_quoted_key {
                            while cursor < text_bytes.len() && text_bytes[cursor].is_ascii_whitespace() {
                                cursor += 1;
                            }
                        } else {
                            while cursor < text_bytes.len() && (text_bytes[cursor] == b' ' || text_bytes[cursor] == b'\t') {
                                cursor += 1;
                            }
                        }

                        if let Some(next_pos) = Self::extract_sensitive_assignment_value(
                            text,
                            text_bytes,
                            key_start,
                            cursor,
                            sep,
                            &mut internal_spans,
                            &mut max_risk,
                            &mut active_yaml_block,
                            &mut json_secret,
                        ) {
                            i = next_pos;
                            continue;
                        }
                    }
                }
                i += 1;
            }
        }

        // 4. URI credentials (://user:password@host, supporting localhost)
        let mut uri_search = 0;
        while let Some(uri_proto) = text[uri_search..].find("://") {
            let abs_proto = uri_search + uri_proto;
            let after_proto = abs_proto + 3;
            let auth_end = text[after_proto..]
                .find(|c: char| c.is_whitespace() || c == '/' || c == '\'' || c == '"')
                .map(|p| after_proto + p)
                .unwrap_or(text.len());

            if let Some(at_pos) = text[after_proto..auth_end].find('@') {
                let abs_at = after_proto + at_pos;
                let user_pass = &text[after_proto..abs_at];
                if let Some(colon_pos) = user_pass.find(':') {
                    let pass_start = after_proto + colon_pos + 1;
                    if pass_start < abs_at {
                        internal_spans.push(InternalSpan {
                            category: "SECRET".to_string(),
                            start: pass_start,
                            end: abs_at,
                            original_sample: "[REDACTED_PASSWORD]".to_string(),
                            replacement: "[REDACTED_SECRET]".to_string(),
                        });
                        max_risk = max_risk.max(0.9);
                    }
                }
            }
            uri_search = auth_end;
        }

        // 5. Email scanner (UTF-8 safe char boundaries)
        let mut s_idx = 0;
        while let Some(at_pos) = text[s_idx..].find('@') {
            let abs_at = s_idx + at_pos;
            let before_at = &text[..abs_at];
            let start = before_at
                .char_indices()
                .rfind(|&(_, c)| c.is_whitespace() || c == ':' || c == '=' || c == '<' || c == '"' || c == '\'' || c == '/')
                .map(|(p, c)| p + c.len_utf8())
                .unwrap_or(0);

            let after_at = &text[abs_at..];
            let end = after_at
                .char_indices()
                .find(|&(_, c)| c.is_whitespace() || c == '>' || c == '"' || c == '\'' || c == ',' || c == ';' || c == ':' || c == '?' || c == '!')
                .map(|(p, _)| abs_at + p)
                .unwrap_or(text.len());

            if start < abs_at && abs_at < end {
                let candidate = &text[start..end];
                if candidate.contains('.') && candidate.len() > 5 {
                    internal_spans.push(InternalSpan {
                        category: "PII_EMAIL".to_string(),
                        start,
                        end,
                        original_sample: "[email]".to_string(),
                        replacement: "[REDACTED_PII]".to_string(),
                    });
                    max_risk = max_risk.max(0.7);
                    s_idx = end;
                    continue;
                }
            }
            s_idx = abs_at + 1;
        }

        // 6. IPv4 scanner (UTF-8 character boundary safe, supporting sentence periods, URLs)
        for (i, _) in text.match_indices('.') {
            let before = &text[..i];
            let ip_start = before
                .char_indices()
                .rfind(|&(_, c)| !c.is_ascii_digit() && c != '.')
                .map(|(p, c)| p + c.len_utf8())
                .unwrap_or(0);

            let after = &text[ip_start..];
            let ip_end = after
                .char_indices()
                .find(|&(_, c)| !c.is_ascii_digit() && c != '.')
                .map(|(p, _)| ip_start + p)
                .unwrap_or(text.len());

            let mut candidate = &text[ip_start..ip_end];
            let mut actual_end = ip_end;
            if candidate.ends_with('.') {
                candidate = &candidate[..candidate.len() - 1];
                actual_end -= 1;
            }

            if candidate.parse::<Ipv4Addr>().is_ok() {
                let mut ctx_start = ip_start.saturating_sub(10);
                while ctx_start > 0 && !text.is_char_boundary(ctx_start) {
                    ctx_start -= 1;
                }
                let ctx = &text[ctx_start..ip_start].to_lowercase();
                if !ctx.contains("version ") && !ctx.trim_end().ends_with('v') {
                    let prev_char = text[..ip_start].chars().last();
                    let next_char = text[actual_end..].chars().next();
                    let left_ok = prev_char.map(|c| !c.is_alphanumeric() && c != '_').unwrap_or(true);
                    let right_ok = next_char.map(|c| !c.is_alphanumeric() && c != '_').unwrap_or(true);
                    if left_ok && right_ok {
                        internal_spans.push(InternalSpan {
                            category: "PII_IPV4".to_string(),
                            start: ip_start,
                            end: actual_end,
                            original_sample: "[ipv4]".to_string(),
                            replacement: "[REDACTED_PII]".to_string(),
                        });
                        max_risk = max_risk.max(0.6);
                    }
                }
            }
        }

        // 7. IPv6 scanner (handling [2001:db8::1], ::ffff:192.0.2.128, etc.)
        for (colon_idx, _) in text.match_indices(':') {
            let before = &text[..colon_idx];
            let ip_start = before
                .char_indices()
                .rfind(|&(_, c)| !c.is_ascii_hexdigit() && c != ':' && c != '.' && c != '[' && c != ']')
                .map(|(p, c)| p + c.len_utf8())
                .unwrap_or(0);

            let after = &text[ip_start..];
            let ip_end = after
                .char_indices()
                .find(|&(_, c)| !c.is_ascii_hexdigit() && c != ':' && c != '.' && c != '[' && c != ']')
                .map(|(p, _)| ip_start + p)
                .unwrap_or(text.len());

            let mut candidate = &text[ip_start..ip_end];
            let mut actual_start = ip_start;
            let mut actual_end = ip_end;
            if candidate.starts_with('[') {
                candidate = &candidate[1..];
                actual_start += 1;
            }
            if candidate.ends_with(']') {
                candidate = &candidate[..candidate.len() - 1];
                actual_end -= 1;
            }

            if candidate.contains(':') && candidate.len() >= 2 && candidate.parse::<Ipv6Addr>().is_ok() {
                let prev_char = text[..actual_start].chars().last();
                let next_char = text[actual_end..].chars().next();
                let left_ok = prev_char.map(|c| !c.is_alphanumeric() && c != '_').unwrap_or(true);
                let right_ok = next_char.map(|c| !c.is_alphanumeric() && c != '_').unwrap_or(true);
                if left_ok && right_ok {
                    internal_spans.push(InternalSpan {
                        category: "PII_IPV6".to_string(),
                        start: actual_start,
                        end: actual_end,
                        original_sample: "[ipv6]".to_string(),
                        replacement: "[REDACTED_PII]".to_string(),
                    });
                    max_risk = max_risk.max(0.6);
                }
            }
        }

        // Deduplicate & sort spans by start position
        internal_spans.sort_by_key(|s| s.start);
        let mut non_overlapping: Vec<InternalSpan> = Vec::new();
        for span in internal_spans {
            if let Some(last) = non_overlapping.last_mut() {
                if span.start < last.end {
                    if span.end > last.end {
                        last.end = span.end;
                    }
                    continue;
                }
            }
            non_overlapping.push(span);
        }

        let ended_in_unquoted_secret = non_overlapping
            .last()
            .map(|s| {
                s.end == text.len()
                    && s.original_sample == "[REDACTED_PASSWORD]"
                    && !text.ends_with('\n')
                    && !text.ends_with('\r')
                    && !text.ends_with('"')
                    && !text.ends_with('\'')
            })
            .unwrap_or(false);

        let ended_in_secret = non_overlapping
            .last()
            .map(|s| {
                s.end == text.len()
                    && s.original_sample != "[REDACTED_PASSWORD]"
                    && s.replacement == "[REDACTED_SECRET]"
                    && !text.ends_with('\n')
                    && !text.ends_with('\r')
                    && !text.ends_with('"')
                    && !text.ends_with('\'')
            })
            .unwrap_or(false);

        let ended_in_ip = non_overlapping
            .last()
            .map(|s| {
                s.end == text.len()
                    && s.category == "PII_IPV4"
                    && !text.ends_with('\n')
                    && !text.ends_with('\r')
            })
            .unwrap_or(false);

        let ended_in_ipv6 = non_overlapping
            .last()
            .map(|s| {
                s.end == text.len()
                    && s.category == "PII_IPV6"
                    && !text.ends_with('\n')
                    && !text.ends_with('\r')
            })
            .unwrap_or(false);

        // Build sanitized string
        let mut sanitized = String::with_capacity(text.len());
        let mut last_idx = 0;
        let mut public_spans = Vec::new();

        for span in &non_overlapping {
            if span.start >= last_idx && span.start <= text.len() && span.end <= text.len() {
                sanitized.push_str(&text[last_idx..span.start]);
                sanitized.push_str(&span.replacement);
                last_idx = span.end;

                public_spans.push(RedactedSpan {
                    category: span.category.clone(),
                    start: span.start,
                    end: span.end,
                    original_sample: span.original_sample.clone(),
                });
            }
        }

        if last_idx < text.len() {
            sanitized.push_str(&text[last_idx..]);
        }

        (sanitized, public_spans, max_risk, ended_in_secret, ended_in_pem, active_yaml_block, ended_in_ip, ended_in_ipv6, ended_in_unquoted_secret, json_secret)
    }
}
