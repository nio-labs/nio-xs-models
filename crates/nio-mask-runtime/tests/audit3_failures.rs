use nio_mask_runtime::NioMask;

fn stream(chunks: &[&str]) -> String {
    let m = NioMask::new();
    let mut out: String = chunks.iter().map(|s| m.sanitize(s).sanitized).collect();
    out.push_str(&m.finish().sanitized);
    out
}

#[test]
fn uppercase_key_must_stitch() {
    let out = stream(&["PASS", "WORD=AlphaSecret123!\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn spaced_assignment_must_stitch() {
    let out = stream(&["pass", "word = AlphaSecret123!\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn spaced_json_assignment_must_stitch() {
    let out = stream(&["{\"pass", "word\" : \"AlphaSecret123!\"}\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn unquoted_yaml_secret_with_spaces_must_remain_secret() {
    let out = stream(&["password: Alpha", " BravoSecret123!\n"]);
    assert!(!out.contains("BravoSecret123!"), "{out:?}");
}

#[test]
fn prefixed_bearer_token_must_buffer_first_character() {
    let out = stream(&["Authorization: Bearer g", "hp_abcdefghijklmnopqrstuvwxyz1234567890\n"]);
    assert!(!out.contains("ghp_abcdefghijklmnopqrstuvwxyz1234567890"), "{out:?}");
}

#[test]
fn uri_scheme_must_stitch_before_colon() {
    let out = stream(&["post", "gres:", "//u:AlphaSecret123!@localhost/status\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn yaml_comment_digit_is_not_an_indentation_indicator() {
    let out = stream(&["password: ", "| # test 9\n  AlphaSecret123!\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn yaml_modifier_must_survive_split_header() {
    let out = stream(&["password: |", "2\n    AlphaSecret123!\n  BravoValueHidden!\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn yaml_split_header_must_preserve_sibling_field() {
    let out = stream(&["credentials:\n  password: ", "|\n    AlphaSecret123!\n  user: public\n"]);
    assert!(out.contains("user: public"), "{out:?}");
}

#[test]
fn yaml_tagged_block_must_hide_body() {
    let out = stream(&["password: !!str |\n  AlphaSecret123!\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn yaml_anchored_block_must_hide_body() {
    let out = stream(&["password: &credential |\n  BravoValueHidden!\n"]);
    assert!(!out.contains("BravoValueHidden!"), "{out:?}");
}
