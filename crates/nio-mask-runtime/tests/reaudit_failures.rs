use nio_mask_runtime::NioMask;

fn stream(chunks: &[&str]) -> String {
    let mask = NioMask::new();
    let mut out: String = chunks.iter().map(|c| mask.sanitize(c).sanitized).collect();
    out.push_str(&mask.finish().sanitized);
    out
}

#[test]
fn minimal_quote_input_must_not_panic() {
    let _ = stream(&["\"="]);
}

#[test]
fn split_json_key_must_hide_password() {
    let out = stream(&["{\"pass", "word\":\"AlphaSecret123!\"}\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn yaml_header_after_split_assignment_must_hide_body() {
    let out = stream(&["password:", " |\n  AlphaSecret123!\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn yaml_split_indentation_must_hide_body() {
    let out = stream(&["password: |\n  ", "AlphaSecret123!\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn yaml_partial_line_must_hide_tail_after_space() {
    let out = stream(&["password: |\n  Alpha", " BravoSecret123!\n"]);
    assert!(!out.contains("BravoSecret123!"), "{out:?}");
}

#[test]
fn yaml_explicit_indentation_must_hide_entire_scalar() {
    let out = stream(&["password: |2\n    AlphaSecret123!\n  BravoValueHidden!\n"]);
    assert!(!out.contains("BravoValueHidden!"), "{out:?}");
}

#[test]
fn multiline_quoted_password_must_hide_second_line() {
    let out = stream(&["password: \"AlphaSecret123!\n  BravoSecret456!\"\n"]);
    assert!(!out.contains("BravoSecret456!"), "{out:?}");
}

#[test]
fn single_character_token_prefix_must_be_held() {
    let out = stream(&["g", "hp_abcdefghijklmnopqrstuvwxyz1234567890\n"]);
    assert!(!out.contains("ghp_abcdefghijklmnopqrstuvwxyz1234567890"), "{out:?}");
}

#[test]
fn split_uri_credentials_must_hide_password() {
    let out = stream(&["postgres://u:", "AlphaSecret123!@localhost/status\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn three_chunk_ip_must_stay_hidden() {
    let out = stream(&["host=1", "92.", "168.1.100\n"]);
    assert_eq!(out, "host=[REDACTED_PII]\n");
}

#[test]
fn ipv4_continuation_must_survive_multiple_calls() {
    let out = stream(&["host=192.168.1.1", "0", "0\n"]);
    assert_eq!(out, "host=[REDACTED_PII]\n");
}

#[test]
fn ipv6_continuation_must_stay_hidden() {
    let out = stream(&["host=2001:db8::1", "234\n"]);
    assert_eq!(out, "host=[REDACTED_PII]\n");
}

#[test]
fn email_continuation_must_not_emit_tld() {
    let out = stream(&["contact ", "alice@example.c", "om\n"]);
    assert_eq!(out, "contact [REDACTED_PII]\n");
}

#[test]
fn finish_must_not_duplicate_stitched_key() {
    let out = stream(&["pass", "word=\"AlphaSecret123!"]);
    assert_eq!(out, "password=\"[REDACTED_SECRET]");
}

#[test]
fn finish_must_preserve_valid_closing_quote() {
    let out = stream(&["password=", "'AlphaSecret123!'"]);
    assert_eq!(out, "password='[REDACTED_SECRET]'");
}

#[test]
fn cli_span_must_reference_the_original_input() {
    let input = "contact alice@example.co";
    let result = std::process::Command::new(env!("CARGO_BIN_EXE_nio-mask-cli"))
        .arg(input).output().unwrap();
    assert!(result.status.success());
    let value: serde_json::Value = serde_json::from_slice(&result.stdout).unwrap();
    let span = &value["spans"][0];
    let start = span["start"].as_u64().unwrap() as usize;
    let end = span["end"].as_u64().unwrap() as usize;
    assert_eq!(&input[start..end], "alice@example.co");
}
