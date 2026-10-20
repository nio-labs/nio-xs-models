use nio_mask_runtime::NioMask;

fn stream(chunks: &[&str]) -> String {
    let m = NioMask::new();
    let mut out: String = chunks.iter().map(|c| m.sanitize(c).sanitized).collect();
    out.push_str(&m.finish().sanitized);
    out
}

#[test]
fn history_limit_must_not_release_an_unfinished_assignment() {
    let first = format!("password{}", " ".repeat(48));
    let out = stream(&[&first, "=AlphaSecret123!\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn token_after_ordinary_whitespace_must_buffer_one_character() {
    let out = stream(&["value g", "hp_abcdefghijklmnopqrstuvwxyz1234567890\n"]);
    assert!(!out.contains("ghp_abcdefghijklmnopqrstuvwxyz1234567890"), "{out:?}");
}

#[test]
fn split_yaml_tag_must_keep_block_context() {
    let out = stream(&["password: !!s", "tr |\n  AlphaSecret123!\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn yaml_property_after_complete_key_must_keep_block_context() {
    let out = stream(&["password: ", "!!str |\n  AlphaSecret123!\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn split_yaml_anchor_must_keep_block_context() {
    let out = stream(&["password: &cred", "ential |\n  AlphaSecret123!\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn json_newline_before_separator_must_hide_password() {
    let out = stream(&["{\"password\"\n: \"AlphaSecret123!\"}\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn json_newline_after_separator_must_hide_password() {
    let out = stream(&["{\"password\":\n  \"AlphaSecret123!\"}\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn ftp_scheme_must_stitch_across_three_chunks() {
    let out = stream(&["f", "tp:", "//u:AlphaSecret123!@localhost/path\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn quoted_password_and_empty_calls_control() {
    let out = stream(&["password=", "", "\"Alpha", "", " BravoSecret123!\"\n"]);
    assert_eq!(out, "password=\"[REDACTED_SECRET]\"\n");
}
