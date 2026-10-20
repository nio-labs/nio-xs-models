"""
Inference & Redaction Pipeline for NioMask (~1.0M Secret & PII Redactor)
Scans text streams, replaces sensitive tokens with redact masks, and preserves clean text and benign hashes.
Features sliding window chunking (>256 bytes), UTF-8 boundary safety, and word-boundary expansion.
"""

import os
import re
import json
import ipaddress
import argparse
import numpy as np
import onnxruntime as ort
from rich.console import Console
from rich.panel import Panel

from model import LABEL_NAMES

console = Console()


class NioMaskRedactor:
    def __init__(self, onnx_model_path: str = "models/nio_mask.onnx"):
        if not os.path.exists(onnx_model_path):
            raise FileNotFoundError(f"Model not found at {onnx_model_path}")

        sess_options = ort.SessionOptions()
        sess_options.intra_op_num_threads = 1
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.session = ort.InferenceSession(onnx_model_path, sess_options, providers=["CPUExecutionProvider"])

    def redact(self, text: str, min_confidence: float = 0.65, min_span_len: int = 4) -> dict:
        raw_bytes = text.encode("utf-8")
        total_len = len(raw_bytes)
        if total_len == 0:
            return {"redacted_text": text, "risk_score": 0.0, "detections": []}

        # 1. Sliding Window ONNX Inference
        window_size = 256
        stride = 192

        if total_len <= window_size:
            windows = [(0, total_len)]
        else:
            windows = []
            pos = 0
            while pos < total_len:
                end = min(pos + window_size, total_len)
                windows.append((pos, end))
                if end == total_len:
                    break
                pos += stride

        global_p_secret = np.zeros(total_len, dtype=np.float32)
        global_p_pii = np.zeros(total_len, dtype=np.float32)
        global_risk = 0.0

        for w_start, w_end in windows:
            w_bytes = raw_bytes[w_start:w_end]
            byte_ids = [b + 4 for b in w_bytes]
            seq_len = len(byte_ids)

            input_ids = np.array([byte_ids], dtype=np.int64)
            attention_mask = np.ones((1, seq_len), dtype=np.float32)

            outputs = self.session.run(None, {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
            })
            token_logits, risk_score = outputs[0], outputs[1]

            # Softmax
            exp_logits = np.exp(token_logits[0] - np.max(token_logits[0], axis=-1, keepdims=True))
            probs = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)

            w_risk = float(risk_score[0, 0])
            if w_risk > global_risk:
                global_risk = w_risk

            for i in range(seq_len):
                idx = w_start + i
                p_s = probs[i, 1] + probs[i, 2]
                p_p = probs[i, 3] + probs[i, 4]
                if p_s > global_p_secret[idx]:
                    global_p_secret[idx] = p_s
                if p_p > global_p_pii[idx]:
                    global_p_pii[idx] = p_p

        # 2. Extract spans (Neural + Pattern Guard)
        candidate_spans = []

        # Neural secret / PII candidate bytes
        i = 0
        while i < total_len:
            if global_p_secret[i] > min_confidence:
                start = i
                while i < total_len and global_p_secret[i] > min_confidence:
                    i += 1
                end = i
                if (end - start) >= min_span_len:
                    candidate_spans.append(("SECRET", start, end, True))
            elif global_p_pii[i] > min_confidence:
                start = i
                while i < total_len and global_p_pii[i] > min_confidence:
                    i += 1
                end = i
                if (end - start) >= min_span_len:
                    candidate_spans.append(("PII", start, end, True))
            else:
                i += 1

        # Identify safe public certificate blocks to prevent false-positive neural hits
        safe_cert_ranges = []
        for m in re.finditer(rb"-----BEGIN CERTIFICATE-----[\s\S]*?-----END CERTIFICATE-----", raw_bytes):
            safe_cert_ranges.append((m.start(), m.end()))

        # Filter out false-positive neural spans inside public certificate blocks
        filtered_candidate_spans = []
        for span_type, start, end, should_expand in candidate_spans:
            if any(c_start <= start and end <= c_end for c_start, c_end in safe_cert_ranges):
                continue
            filtered_candidate_spans.append((span_type, start, end, should_expand))
        candidate_spans = filtered_candidate_spans

        # Pattern Guard: Standard API key / secret patterns
        # Escaped JSON / YAML sensitive keys (e.g. "pass\u0077ord": ... or "\u0070assword": ...)
        sensitive_key_names = {
            "password", "passwd", "pwd", "secret", "api_key", "token", "github_token", "aws_secret_access_key"
        }
        json_key_pat = re.compile(rb'"((?:[^"\\]|\\[\s\S])*)"\s*([:=])')
        json_assignments = []
        for m in json_key_pat.finditer(raw_bytes):
            if any(start <= m.start() < end for start, end in json_assignments):
                continue
            decoded_key = None
            try:
                decoded_key = json.loads(b'"' + m.group(1) + b'"')
            except Exception:
                pass
            if decoded_key is None:
                try:
                    # YAML escaped line breaks suppress the following indentation.
                    folded_key = re.sub(rb"\\\r?\n[ \t]*", b"", m.group(1))
                    decoded_key = folded_key.decode("unicode_escape")
                except Exception:
                    pass
            if not isinstance(decoded_key, str) or decoded_key.lower() not in sensitive_key_names:
                continue

            pos = m.end()
            sep = m.group(2)
            is_json_context = sep == b":" and (
                raw_bytes[:m.start()].rstrip().endswith(b"{") or raw_bytes[:m.start()].rstrip().endswith(b",")
            )
            if is_json_context:
                value_start = pos
                while value_start < total_len and raw_bytes[value_start] in b" \t\r\n":
                    value_start += 1
                try:
                    # Decode one complete value, including nested containers and
                    # escaped strings, while keeping byte offsets for spans.
                    value_text = raw_bytes[value_start:].decode("utf-8")
                    _, value_chars = json.JSONDecoder().raw_decode(value_text)
                    value_end = value_start + len(value_text[:value_chars].encode("utf-8"))
                except (ValueError, UnicodeError):
                    pass
                else:
                    if raw_bytes[value_start:value_start + 1] == b'"':
                        candidate_spans.append(("SECRET", value_start + 1, value_end - 1, False))
                    else:
                        candidate_spans.append(("SECRET", value_start, value_end, False, '"[REDACTED_SECRET]"'))
                    json_assignments.append((m.start(), value_end))
                    global_risk = max(global_risk, 0.95)
                    continue
            # 1. Double-quoted value
            m_dquote = re.match(rb'\s*(?:(?:!!?[^\s\r\n]+|&[^\s\r\n]+)\s*)*"((?:[^"\\]|\\.)*)"', raw_bytes[pos:])
            if m_dquote:
                candidate_spans.append(("SECRET", pos + m_dquote.start(1), pos + m_dquote.end(1), False))
                global_risk = max(global_risk, 0.95)
                continue

            # 2. Single-quoted value
            m_squote = re.match(rb"\s*(?:(?:!!?[^\s\r\n]+|&[^\s\r\n]+)\s*)*'((?:[^'\\]|\\.|'')*)'", raw_bytes[pos:])
            if m_squote:
                candidate_spans.append(("SECRET", pos + m_squote.start(1), pos + m_squote.end(1), False))
                global_risk = max(global_risk, 0.95)
                continue

            # 3. YAML block scalar (if colon)
            if sep == b":":
                m_block = re.match(rb"\s*(?:(?:!!?[^\s\r\n]+|&[^\s\r\n]+)\s*)*(?:[|>-]([0-9+-]*))?[ \t]*(?:#[^\r\n]*)?\r?\n", raw_bytes[pos:])
                if m_block:
                    line_start = raw_bytes.rfind(b"\n", 0, m.start()) + 1
                    parent_indent = m.start() - line_start
                    block_pos = pos + m_block.end()
                    block_indent = None
                    has_block_indicator = bool(re.search(rb"[|>]", m_block.group(0)))
                    mod = m_block.group(1) if m_block.group(1) else b""
                    for b in mod:
                        if ord(b'1') <= b <= ord(b'9'):
                            block_indent = parent_indent + (b - ord(b'0'))
                            break
                    while block_pos < total_len:
                        nl = raw_bytes.find(b"\n", block_pos)
                        line_end = nl if nl != -1 else total_len
                        line = raw_bytes[block_pos:line_end].rstrip(b"\r")
                        stripped = line.lstrip(b" \t")
                        if not stripped:
                            if nl == -1:
                                break
                            block_pos = nl + 1
                            continue
                        indent = len(line) - len(stripped)
                        if block_indent is None and stripped.startswith(b"#") and (indent <= parent_indent or not has_block_indicator):
                            if nl == -1:
                                break
                            block_pos = nl + 1
                            continue
                        if block_indent is None:
                            if indent > parent_indent:
                                if not has_block_indicator and (stripped.startswith(b'"') or stripped.startswith(b"'")):
                                    break
                                block_indent = indent
                            else:
                                break
                        if indent < block_indent:
                            break
                        v_start = block_pos + indent
                        v_end = block_pos + len(line)
                        if not has_block_indicator:
                            comment_match = re.search(rb"[ \t]+#[^\r\n]*$", line)
                            if comment_match:
                                v_end = block_pos + comment_match.start()
                        candidate_spans.append(("SECRET", v_start, v_end, False))
                        global_risk = max(global_risk, 0.95)
                        if nl == -1:
                            break
                        block_pos = nl + 1
                    continue

            # 4. Inline tagged unquoted YAML assignment
            if sep == b":":
                m_tagged = re.match(rb"\s*(?:(?:!!?[^\s\r\n]+|&[^\s\r\n]+)\s+)+([^\s\"'\r\n][^\r\n]*?)(?=\s*(?:[\r\n]|$))", raw_bytes[pos:])
                if m_tagged:
                    candidate_spans.append(("SECRET", pos + m_tagged.start(1), pos + m_tagged.end(1), False))
                    global_risk = max(global_risk, 0.95)
                    continue

            # 5. Plain unquoted value
            is_json_context = sep == b":" and (
                raw_bytes[:m.start()].rstrip().endswith(b"{") or raw_bytes[:m.start()].rstrip().endswith(b",")
            )
            if sep == b"=":
                m_unquoted = re.match(rb"\s*([^\s\"'\r\n][^\r\n]*?)(?=\s*(?:[\r\n]|$))", raw_bytes[pos:])
                if m_unquoted:
                    candidate_spans.append(("SECRET", pos + m_unquoted.start(1), pos + m_unquoted.end(1), False))
                    global_risk = max(global_risk, 0.95)
                    continue
            elif sep == b":":
                if is_json_context:
                    m_unquoted = re.match(rb"\s*([^\s\"'\r\n,{}][^\r\n,{}]*?)(?=\s*(?:[,\r\n}]|$))", raw_bytes[pos:])
                    if m_unquoted:
                        candidate_spans.append(("SECRET", pos + m_unquoted.start(1), pos + m_unquoted.end(1), False, '"[REDACTED_SECRET]"'))
                        global_risk = max(global_risk, 0.95)
                        continue
                else:
                    m_unquoted = re.match(rb"\s*(?!(?:(?:!!?[^\s\r\n]+|&[^\s\r\n]+)\s*)*(?:[|>-][0-9+-]*\s*)?(?:#[^\r\n]*)?\r?\n)([^\s\"'\r\n][^\r\n]*?)(?=\s*(?:[\r\n]|$))", raw_bytes[pos:])
                    if m_unquoted:
                        candidate_spans.append(("SECRET", pos + m_unquoted.start(1), pos + m_unquoted.end(1), False))
                        global_risk = max(global_risk, 0.95)
                        continue

        # YAML block scalar: password: |\n ... (multiline support, tags & anchors support, and following-line plain scalars)
        yaml_block_hdr = re.compile(
            rb"""(?:"(?:password|passwd|pwd|secret|api_key|token)"|'(?:password|passwd|pwd|secret|api_key|token)'|(?:password|passwd|pwd|secret|api_key|token))\s*:\s*(?:(?:!!?[^\s\r\n]+|&[^\s\r\n]+)\s*)*(?:[|>-]([0-9+-]*))?[ \t]*(?:#[^\r\n]*)?\r?\n""",
            re.IGNORECASE
        )
        for m in yaml_block_hdr.finditer(raw_bytes):
            line_start = raw_bytes.rfind(b"\n", 0, m.start()) + 1
            parent_indent = m.start() - line_start
            pos = m.end()
            block_indent = None
            has_block_indicator = bool(re.search(rb"[|>]", m.group(0)))
            mod = m.group(1) if m.group(1) else b""
            for b in mod:
                if ord(b'1') <= b <= ord(b'9'):
                    block_indent = parent_indent + (b - ord(b'0'))
                    break
            while pos < total_len:
                nl = raw_bytes.find(b"\n", pos)
                line_end = nl if nl != -1 else total_len
                line = raw_bytes[pos:line_end].rstrip(b"\r")
                stripped = line.lstrip(b" \t")
                if not stripped:
                    if nl == -1:
                        break
                    pos = nl + 1
                    continue
                indent = len(line) - len(stripped)
                if block_indent is None and stripped.startswith(b"#") and (indent <= parent_indent or not has_block_indicator):
                    if nl == -1:
                        break
                    pos = nl + 1
                    continue
                if block_indent is None:
                    if indent > parent_indent:
                        if not has_block_indicator and (stripped.startswith(b'"') or stripped.startswith(b"'")):
                            break
                        block_indent = indent
                    else:
                        break
                if indent < block_indent:
                    break
                v_start = pos + indent
                v_end = pos + len(line)
                if not has_block_indicator:
                    comment_match = re.search(rb"[ \t]+#[^\r\n]*$", line)
                    if comment_match:
                        v_end = pos + comment_match.start()
                candidate_spans.append(("SECRET", v_start, v_end, False))
                global_risk = max(global_risk, 0.95)
                if nl == -1:
                    break
                pos = nl + 1

        key_prefix = rb"""(?:"(?:password|passwd|pwd|secret|api_key|token)"|'(?:password|passwd|pwd|secret|api_key|token)'|(?:password|passwd|pwd|secret|api_key|token))"""

        secret_patterns = [
            re.compile(rb"AKIA[A-Z0-9]{16}"),
            re.compile(rb"AWS_SECRET_ACCESS_KEY=['\"]?([A-Za-z0-9/+=]{40})['\"]?"),
            re.compile(rb"ghp_[A-Za-z0-9]{36,}"),
            re.compile(rb"github_pat_[A-Za-z0-9_]{40,}"),
            re.compile(rb"sk-proj-[A-Za-z0-9_\-]{30,}"),
            re.compile(rb"sk-[A-Za-z0-9_\-]{30,}"),
            re.compile(rb"sk_live_[A-Za-z0-9]{24,}"),
            re.compile(rb"xoxb-[0-9]{10,}-[0-9]{10,}-[A-Za-z0-9]{20,}"),
            re.compile(rb"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z0-9 ]*PRIVATE KEY-----"),
            # JSON / Double-quoted assignment with escape support and optional YAML tag/anchor prefix
            re.compile(key_prefix + rb'''\s*[:=]\s*(?:(?:!!?[^\s\r\n]+|&[^\s\r\n]+)\s*)*"((?:[^"\\]|\\.)*)"''', re.IGNORECASE),
            # Single-quoted assignment with YAML doubled single-quote support and optional YAML tag/anchor prefix
            re.compile(key_prefix + rb"""\s*[:=]\s*(?:(?:!!?[^\s\r\n]+|&[^\s\r\n]+)\s*)*'((?:[^'\\]|\\.|'')*)'""", re.IGNORECASE),
            # Inline tagged unquoted YAML assignment (e.g. password: !!str AlphaSecret123!)
            re.compile(key_prefix + rb"""\s*:\s*(?:(?:!!?[^\s\r\n]+|&[^\s\r\n]+)\s+)+([^\s"'\r\n][^\r\n]*?)(?=\s*(?:[\r\n]|$))""", re.IGNORECASE),
            # Unquoted = assignment (env, shell, URL query)
            re.compile(key_prefix + rb"""\s*=\s*([^\s"'\r\n][^\r\n]*?)(?=\s*(?:[\r\n]|$))""", re.IGNORECASE),
            # Unquoted : assignment in YAML / JSON (ending before newline or EOF, excluding block / next-line scalar headers)
            re.compile(key_prefix + rb"""\s*:\s*(?!(?:(?:!!?[^\s\r\n]+|&[^\s\r\n]+)\s*)*(?:[|>-][0-9+-]*\s*)?(?:#[^\r\n]*)?\r?\n)([^\s"'\r\n][^\r\n]*?)(?=\s*(?:[\r\n]|$))""", re.IGNORECASE),
            re.compile(rb"://[^:\s/@]+:([^@\s/]+)@"),  # URI credentials
        ]

        for pat in secret_patterns:
            for m in pat.finditer(raw_bytes):
                # JSON has already supplied the complete value span. A legacy
                # assignment match must not extend it through sibling fields.
                if any(start <= m.start() < end for start, end in json_assignments):
                    continue
                if pat.groups > 0 and m.lastindex:
                    candidate_spans.append(("SECRET", m.start(m.lastindex), m.end(m.lastindex), False))
                else:
                    candidate_spans.append(("SECRET", m.start(), m.end(), False))
                global_risk = max(global_risk, 0.95)

        # Pattern Guard: Email
        email_pat = re.compile(rb"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
        for m in email_pat.finditer(raw_bytes):
            candidate_spans.append(("PII", m.start(), m.end(), False))
            global_risk = max(global_risk, 0.70)

        # Pattern Guard: Phone & SSN
        pii_patterns = [
            re.compile(rb"""\bphone\s*[:=]\s*([+0-9][-0-9\s()]{7,}[0-9])""", re.IGNORECASE),
            re.compile(rb"""\bssn\s*[:=]\s*([0-9]{3}-[0-9]{2}-[0-9]{4})\b""", re.IGNORECASE),
        ]
        for pat in pii_patterns:
            for m in pat.finditer(raw_bytes):
                candidate_spans.append(("PII", m.start(1), m.end(1), False))
                global_risk = max(global_risk, 0.65)

        # Pattern Guard: Bracketed IPv6 (e.g. https://[2001:db8::1]/status, host=[fe80::1])
        bracketed_ipv6_pat = re.compile(rb"\[([0-9a-fA-F:.]+)\]")
        for m in bracketed_ipv6_pat.finditer(raw_bytes):
            val_bytes = m.group(1)
            token_str = val_bytes.decode("ascii", errors="ignore")
            try:
                ip = ipaddress.ip_address(token_str)
                if isinstance(ip, ipaddress.IPv6Address):
                    candidate_spans.append(("PII", m.start(1), m.end(1), False))
                    global_risk = max(global_risk, 0.60)
            except ValueError:
                pass

        # Pattern Guard: IP addresses (IPv4 & IPv6 with standard ipaddress parsing, URLs like https://192.168.1.100/status)
        ip_candidate_pat = re.compile(
            rb"(?:(?<=[/=:\s\"'@\[])|^)([0-9a-fA-F:.]*::[0-9a-fA-F:.]*|(?:[0-9]{1,3}\.){3}[0-9]{1,3}|(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4})(?=[/?#:\s\"'\]).,;]|$)"
        )
        for m in ip_candidate_pat.finditer(raw_bytes):
            val_bytes = m.group(1)
            token_str = val_bytes.decode("ascii", errors="ignore")
            clean_str = token_str.rstrip(".")
            ctx_start = max(0, m.start(1) - 10)
            ctx = raw_bytes[ctx_start:m.start(1)].lower()
            if b"version " in ctx or ctx.rstrip().endswith(b"v"):
                continue

            try:
                ip = ipaddress.ip_address(clean_str)
                if (":" in clean_str or clean_str.count(".") == 3) and len(clean_str) >= 2:
                    cand_start = m.start(1)
                    cand_end = cand_start + len(clean_str.encode("ascii"))
                    candidate_spans.append(("PII", cand_start, cand_end, False))
                    global_risk = max(global_risk, 0.60)
            except ValueError:
                pass

        # 3. Align spans to valid UTF-8 character boundaries & word boundaries
        char_boundaries = set()
        b_idx = 0
        for ch in text:
            char_boundaries.add(b_idx)
            b_idx += len(ch.encode("utf-8"))
        char_boundaries.add(total_len)

        aligned_spans = []
        delimiters = set(b" \t\n\r'\"`;,&=<>{}@/?#")

        for item in candidate_spans:
            span_type = item[0]
            start = item[1]
            end = item[2]
            should_expand = item[3]
            custom_placeholder = item[4] if len(item) > 4 else None

            # Expand to valid UTF-8 boundary
            while start > 0 and start not in char_boundaries:
                start -= 1
            while end < total_len and end not in char_boundaries:
                end += 1

            # If secret, expand to token boundary if partial token detected
            if should_expand and span_type == "SECRET" and not raw_bytes[start:end].startswith(b"-----"):
                while end < total_len and raw_bytes[end] not in delimiters:
                    end += 1
                while end < total_len and end not in char_boundaries:
                    end += 1

            aligned_spans.append((span_type, start, end, custom_placeholder))

        # 4. Deduplicate and sort spans
        aligned_spans.sort(key=lambda s: s[1])
        merged_spans = []
        for span in aligned_spans:
            if not merged_spans:
                merged_spans.append(span)
                continue
            prev_type, prev_start, prev_end, prev_custom = merged_spans[-1]
            curr_type, curr_start, curr_end, curr_custom = span
            if curr_start <= prev_end:
                new_type = "SECRET" if (prev_type == "SECRET" or curr_type == "SECRET") else "PII"
                merged_spans[-1] = (new_type, prev_start, max(prev_end, curr_end), prev_custom or curr_custom)
            else:
                merged_spans.append(span)

        # 5. Construct sanitized output and detections (DO NOT LEAK ORIGINAL SENSITIVE VALUE IN METADATA)
        detections = []
        redacted_bytes = bytearray()
        last_idx = 0

        for span_type, start, end, custom_placeholder in merged_spans:
            if start >= last_idx:
                redacted_bytes.extend(raw_bytes[last_idx:start])
                placeholder = custom_placeholder if custom_placeholder else ("[REDACTED_SECRET]" if span_type == "SECRET" else "[REDACTED_PII]")
                detections.append({
                    "type": span_type,
                    "start": start,
                    "end": end,
                    "value": placeholder,  # Masked placeholder: zero plaintext leak
                })
                redacted_bytes.extend(placeholder.encode("utf-8"))
                last_idx = end

        if last_idx < total_len:
            redacted_bytes.extend(raw_bytes[last_idx:])

        redacted_text = redacted_bytes.decode("utf-8", errors="replace")
        return {
            "redacted_text": redacted_text,
            "risk_score": float(global_risk),
            "detections": detections,
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="models/nio_mask.onnx")
    parser.add_argument("--text", type=str, help="Text to sanitize")
    args = parser.parse_args()

    redactor = NioMaskRedactor(args.model)

    if args.text:
        res = redactor.redact(args.text)
        console.print(Panel(res["redacted_text"], title=f"Sanitized (Risk: {res['risk_score']:.2f})"))
    else:
        test_inputs = [
            "export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE && export GITHUB_TOKEN=ghp_kY4V9wM28N1z4F817B238491028301928491",
            "curl -H 'Authorization: Bearer sk-proj-ab12cd34ef56gh78ij90kl12mn34op56qr78st90uv12wx34' https://api.openai.com/v1",
            "Connecting to PostgreSQL database at postgres://admin:SuperSecretPass123!@192.168.1.100:5432/production_db",
            "git commit 4b825dc642cb6eb9a060e54bf8d69288fbee4904 (Merge pull request #42 from feature-branch)",
            "fn main() { println!(\"Hello edge world!\"); }",
        ]

        console.print("[bold cyan]Running NioMask Redaction Demos:[/bold cyan]\n")
        for text in test_inputs:
            console.print(f"[bold dim]Input:[/bold dim]  {text}")
            res = redactor.redact(text)
            risk_color = "red" if res["risk_score"] > 0.6 else ("yellow" if res["risk_score"] > 0.2 else "green")
            console.print(f"[bold dim]Output:[/bold dim] [{risk_color}]{res['redacted_text']}[/{risk_color}] (Risk: [{risk_color}]{res['risk_score']:.3f}[/{risk_color}])")
            if res["detections"]:
                console.print(f"[bold dim]Caught:[/bold dim] {res['detections']}")
            console.print("-" * 70)


if __name__ == "__main__":
    main()
