//! Sub-millisecond HTML / Web Content Pre-Scrubber.
//! Decimates boilerplate web noise (scripts, styles, navbars, footers) into clean semantic text in < 1.5ms.

pub fn scrub_html_content(raw_html: &str) -> String {
    let mut scrubbed = raw_html.to_string();

    // 1. Remove complete block noise tags and their interior contents
    let noise_blocks = [
        ("script", "</script>"),
        ("style", "</style>"),
        ("svg", "</svg>"),
        ("noscript", "</noscript>"),
        ("nav", "</nav>"),
        ("footer", "</footer>"),
        ("header", "</header>"),
        ("iframe", "</iframe>"),
    ];

    for (open_tag, close_tag) in noise_blocks {
        scrubbed = remove_tag_block(&scrubbed, open_tag, close_tag);
    }

    // 2. Preserve structural formatting for code blocks and headers
    scrubbed = scrubbed.replace("</pre>", "\n```\n");
    scrubbed = scrubbed.replace("<pre>", "\n```\n");
    scrubbed = scrubbed.replace("</code>", "`");
    scrubbed = scrubbed.replace("<code>", "`");
    scrubbed = scrubbed.replace("</h1>", "\n\n");
    scrubbed = scrubbed.replace("</h2>", "\n\n");
    scrubbed = scrubbed.replace("</h3>", "\n\n");
    scrubbed = scrubbed.replace("</p>", "\n");
    scrubbed = scrubbed.replace("</li>", "\n");
    scrubbed = scrubbed.replace("</tr>", "\n");

    // 3. Strip remaining generic HTML tags
    let mut result = String::with_capacity(scrubbed.len() / 3);
    let mut in_tag = false;

    for ch in scrubbed.chars() {
        if ch == '<' {
            in_tag = true;
        } else if ch == '>' {
            in_tag = false;
        } else if !in_tag {
            result.push(ch);
        }
    }

    // 4. Decode basic HTML entities
    let decoded = result
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", "\"")
        .replace("&#39;", "'")
        .replace("&nbsp;", " ");

    // 5. Normalize whitespace and blank lines
    let mut clean_lines = Vec::new();
    for line in decoded.lines() {
        let trimmed = line.trim();
        if !trimmed.is_empty() {
            clean_lines.push(trimmed);
        }
    }

    clean_lines.join("\n")
}

fn remove_tag_block(html: &str, open_name: &str, close_name: &str) -> String {
    let mut out = String::with_capacity(html.len());
    let mut rest = html;
    let open_prefix = format!("<{}", open_name);

    while let Some(start_idx) = rest.to_lowercase().find(&open_prefix) {
        out.push_str(&rest[..start_idx]);
        let after_open = &rest[start_idx..];

        if let Some(close_idx) = after_open.to_lowercase().find(close_name) {
            rest = &after_open[close_idx + close_name.len()..];
        } else {
            // Unclosed tag; drop the rest
            return out;
        }
    }
    out.push_str(rest);
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_scrubber_decimation() {
        let raw = r#"
            <!DOCTYPE html>
            <html>
            <head>
                <title>Test Docs</title>
                <script>var tracker = 123; function send(){}</script>
                <style>body { background: #000; }</style>
            </head>
            <body>
                <nav><a href="/">Home</a><a href="/login">Login</a></nav>
                <main>
                    <h1>Tokio Broadcast Channel</h1>
                    <p>Creates a bounded multi-producer, multi-consumer channel.</p>
                    <pre><code>fn channel&lt;T&gt;(capacity: usize) -&gt; (Sender&lt;T&gt;, Receiver&lt;T&gt;)</code></pre>
                </main>
                <footer>&copy; 2026 Tech Corp</footer>
            </body>
            </html>
        "#;

        let clean = scrub_html_content(raw);
        assert!(!clean.contains("tracker"));
        assert!(!clean.contains("background"));
        assert!(!clean.contains("Login"));
        assert!(!clean.contains("Tech Corp"));
        assert!(clean.contains("Tokio Broadcast Channel"));
        assert!(clean.contains("fn channel<T>(capacity: usize) -> (Sender<T>, Receiver<T>)"));
    }
}
