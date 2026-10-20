use nio_mask_runtime::NioMask;

fn stream(chunks: &[&str]) -> String {
    let mask = NioMask::new();
    chunks.iter().map(|c| mask.sanitize(c).sanitized).collect()
}

#[test]
fn yaml_stream_must_hide_body() {
    assert!(!stream(&["password: |\n", "  AlphaSecret123!\n"]).contains("AlphaSecret123!"));
}
#[test]
fn yaml_blank_must_not_end_block() {
    assert!(!stream(&["password: |\n  AlphaSecret123!\n\n  BravoSecret456!\n"]).contains("BravoSecret456!"));
}
#[test]
fn yaml_chomp_header_must_hide_body() {
    assert!(!stream(&["password: |-\n  AlphaSecret123!\n"]).contains("AlphaSecret123!"));
}
#[test]
fn quoted_password_space_must_stay_secret() {
    assert!(!stream(&["password=\"Alpha", " BravoSecret123!\"\n"]).contains("BravoSecret123!"));
}
#[test]
fn quote_escape_must_survive_chunk_boundary() {
    assert!(!stream(&["password=", "\"Alpha\\", "\"BravoSecret123!\"\n"]).contains("BravoSecret123!"));
}
#[test]
fn yaml_doubled_quote_must_survive_boundary() {
    assert!(!stream(&["password=", "'Alpha'", "'BravoSecret123!'\n"]).contains("BravoSecret123!"));
}
#[test]
fn json_key_split_must_hide_password() {
    assert!(!stream(&["{\"password\":", "\"AlphaSecret123!\"}\n"]).contains("AlphaSecret123!"));
}
#[test]
fn standalone_token_split_must_hide_pat() {
    assert!(!stream(&["gh", "p_abcdefghijklmnopqrstuvwxyz1234567890\n"]).contains("ghp_abcdefghijklmnopqrstuvwxyz1234567890"));
}
#[test]
fn yaml_dedent_must_preserve_sibling() {
    assert!(stream(&["credentials:\n  password: |\n    AlphaSecret123!\n  username: safeuser\n"]).contains("username: safeuser"));
}
#[test]
fn complete_ip_must_be_redacted_at_eof() {
    assert_eq!(stream(&["host=192.168.1.1"]), "host=[REDACTED_PII]");
}
