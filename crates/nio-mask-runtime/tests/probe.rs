use nio_mask_runtime::NioMask;

#[test]
fn test_all_probe_single_cases() {
    let cases = [
        ("unicode_ipv4_context", "สวัสดี host=192.168.1.100\n", "สวัสดี host=[REDACTED_PII]\n"),
        ("json_password", "{\"password\":\"SuperSecretPass123!\"}\n", "{\"password\":\"[REDACTED_SECRET]\"}\n"),
        ("yaml_password", "password: SuperSecretPass123!\n", "password: [REDACTED_SECRET]\n"),
        ("quoted_password", "password=\"SuperSecretPass123!\"\n", "password=\"[REDACTED_SECRET]\"\n"),
        ("json_escaped_quote", "{\"password\":\"Alpha\\\"BravoSecret123!\"}\n", "{\"password\":\"[REDACTED_SECRET]\"}\n"),
        ("unfinished_benign", "password=", "password="),
        ("short_pat_at_eof", "token=ghp_abcdefghijklmnop", "token=[REDACTED_SECRET]"),
        ("aws_secret", "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n", "AWS_SECRET_ACCESS_KEY=[REDACTED_SECRET]\n"),
        ("ipv6_mapped", "host=::ffff:192.0.2.128\n", "host=[REDACTED_PII]\n"),
        ("ipv6_url", "https://[2001:db8::1]/status\n", "https://[[REDACTED_PII]]/status\n"),
        ("uri_localhost", "postgres://u:FirstPass123@localhost\n", "postgres://u:[REDACTED_SECRET]@localhost\n"),
        ("uri_localhost_eof", "postgres://u:FirstPass123@localhost", "postgres://u:[REDACTED_SECRET]@localhost"),
        ("pem_then_text", "-----BEGIN PRIVATE KEY-----\nAbCdEf123\n-----END PRIVATE KEY----- keep-this\n", "[REDACTED_SECRET] keep-this\n"),
        ("benign_secret_word", "This is a secret", "This is a secret"),
        // Additional singles from 1830af4 review
        ("host_without_newline", "host=192.168.1.100", "host=[REDACTED_PII]"),
        ("email_without_newline", "contact alice@example.com", "contact [REDACTED_PII]"),
        ("benign_host_without_newline", "host=localhost", "host=localhost"),
        ("benign_partial_key", "p", "p"),
        ("quoted_aws_secret", "AWS_SECRET_ACCESS_KEY=\"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\"\n", "AWS_SECRET_ACCESS_KEY=\"[REDACTED_SECRET]\"\n"),
        ("yaml_multiline", "password: |\n  AlphaSecret123!\n  BravoSecret456!\n", "password: |\n  [REDACTED_SECRET]\n  [REDACTED_SECRET]\n"),
        ("single_quoted_value", "password='AlphaSecret123!'\n", "password='[REDACTED_SECRET]'\n"),
    ];

    for (name, input, expected) in cases {
        let r = NioMask::new().sanitize(input);
        assert_eq!(r.sanitized, expected, "Failed case: {name}");
    }
}

#[test]
fn test_all_probe_stream_cases() {
    let stream_cases = [
        ("pat", "token=ghp_abcdefghijklmnopqrstuvwxyz1234567890\n", "token=[REDACTED_SECRET]\n"),
        ("password", "password=SuperSecretPass123!\n", "password=[REDACTED_SECRET]\n"),
        ("quoted_password", "password=\"SuperSecretPass123!\"\n", "password=\"[REDACTED_SECRET]\"\n"),
        ("email", "contact alice@example.com\n", "contact [REDACTED_PII]\n"),
        ("ipv4", "host=192.168.1.100\n", "host=[REDACTED_PII]\n"),
        ("ipv6", "host=2001:db8::1\n", "host=[REDACTED_PII]\n"),
        ("pem", "-----BEGIN RSA PRIVATE KEY-----\nAbCdEf123456789\n-----END RSA PRIVATE KEY-----\n", "[REDACTED_SECRET]"),
    ];

    for (name, input, expected) in stream_cases {
        for split in 0..=input.len() {
            if !input.is_char_boundary(split) {
                continue;
            }
            let m = NioMask::new();
            let s1 = m.sanitize(&input[..split]).sanitized;
            let s2 = m.sanitize(&input[split..]).sanitized;
            let combined = format!("{s1}{s2}");
            assert_eq!(combined, expected, "Failed stream case {name} at split {split}: {combined:?} != {expected:?}");
        }
    }
}

#[test]
fn test_all_probe_explicit_streams() {
    let explicit: [(&str, &[&str], &str); 9] = [
        ("three_chunk_pat", &["token=ghp_abcdefghijklmnop", "qrstuv", "wxyz1234567890\n"], "token=[REDACTED_SECRET]\n"),
        ("empty_chunk_pat", &["token=ghp_abcdefghijklmnop", "", "qrstuvwxyz1234567890\n"], "token=[REDACTED_SECRET]\n"),
        ("three_chunk_password", &["password=", "AlphaSecret", "BravoSecret123!\n"], "password=[REDACTED_SECRET]\n"),
        ("three_chunk_email", &["contact ", "alice", "@example.com\n"], "contact [REDACTED_PII]\n"),
        ("three_chunk_host", &["host=", "192.", "168.1.100\n"], "host=[REDACTED_PII]\n"),
        ("benign_split_host", &["host=", "localhost\n"], "host=localhost\n"),
        ("benign_split_contact", &["contact ", "support\n"], "contact support\n"),
        ("single_quote_stream", &["password=", "'AlphaSecret123!'\n"], "password='[REDACTED_SECRET]'\n"),
        ("escaped_quote_stream", &["password=", "\"Alpha\\\"BravoSecret123!\"\n"], "password=\"[REDACTED_SECRET]\"\n"),
    ];

    for (name, chunks, expected) in explicit {
        let m = NioMask::new();
        let mut actual = String::new();
        for chunk in chunks {
            actual.push_str(&m.sanitize(chunk).sanitized);
        }
        assert_eq!(actual, expected, "Failed explicit stream: {name}");
    }
}

#[test]
fn test_all_context_split_matrix() {
    let contexts = [
        ("github_env", "GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz1234567890\n", "GITHUB_TOKEN=[REDACTED_SECRET]\n"),
        ("email_field", "email=alice@example.com\n", "email=[REDACTED_PII]\n"),
        ("peer_field", "peer=192.168.1.100\n", "peer=[REDACTED_PII]\n"),
    ];

    for (name, input, expected) in contexts {
        let mut passing = 0;
        let mut total = 0;
        for split in 0..=input.len() {
            if !input.is_char_boundary(split) {
                continue;
            }
            total += 1;
            let m = NioMask::new();
            let actual = format!("{}{}", m.sanitize(&input[..split]).sanitized, m.sanitize(&input[split..]).sanitized);
            assert_eq!(actual, expected, "Failed context split {name} at split {split}: {actual:?} != {expected:?}");
            if actual == expected {
                passing += 1;
            }
        }
        assert_eq!(passing, total, "{name} passed {passing}/{total} splits");
    }
}

#[test]
fn test_all_three_chunk_matrix() {
    let triples = [
        ("pat", "token=ghp_abcdefghijklmnopqrstuvwxyz1234567890\n", "token=[REDACTED_SECRET]\n"),
        ("password", "password=SuperSecretPass123!\n", "password=[REDACTED_SECRET]\n"),
    ];

    for (name, input, expected) in triples {
        let mut passing = 0;
        let mut total = 0;
        for a in 1..input.len() {
            if !input.is_char_boundary(a) {
                continue;
            }
            for b in (a + 1)..input.len() {
                if !input.is_char_boundary(b) {
                    continue;
                }
                total += 1;
                let m = NioMask::new();
                let actual = format!(
                    "{}{}{}",
                    m.sanitize(&input[..a]).sanitized,
                    m.sanitize(&input[a..b]).sanitized,
                    m.sanitize(&input[b..]).sanitized
                );
                assert_eq!(
                    actual, expected,
                    "Failed {name} a={a} b={b}: {:?} + {:?} + {:?} -> {actual:?} != {expected:?}",
                    &input[..a], &input[a..b], &input[b..]
                );
                if actual == expected {
                    passing += 1;
                }
            }
        }
        assert_eq!(passing, total, "{name} passed {passing}/{total} splits");
    }
}
