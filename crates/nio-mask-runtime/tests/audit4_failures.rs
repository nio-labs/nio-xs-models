use nio_mask_runtime::NioMask;

fn stream(chunks: &[&str]) -> String {
    let m = NioMask::new();
    let mut out: String = chunks.iter().map(|c| m.sanitize(c).sanitized).collect();
    out.push_str(&m.finish().sanitized);
    out
}

#[test]
fn unicode_history_truncation_must_preserve_char_boundaries() {
    let input = format!("é{}", "a".repeat(47));
    assert_eq!(stream(&[&input]), input);
}

#[test]
fn unicode_history_search_must_preserve_char_boundaries() {
    assert_eq!(stream(&["你好", " world\n"]), "你好 world\n");
}

#[test]
fn complete_key_followed_by_space_must_stitch() {
    let out = stream(&["password ", "= AlphaSecret123!\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn complete_quoted_key_followed_by_space_must_stitch() {
    let out = stream(&["{\"password\"", " : \"AlphaSecret123!\"}\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn uppercase_key_with_partial_api_prefix_must_preserve_context() {
    let out = stream(&["PASSWORD=A", "lphaSecret123!\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn passwd_key_with_partial_api_prefix_must_preserve_context() {
    let out = stream(&["passwd=gh", "p_abcdefghijklmnopqrstuvwxyz1234567890\n"]);
    assert_eq!(out, "passwd=[REDACTED_SECRET]\n");
}

#[test]
fn bearer_context_must_survive_three_chunks() {
    let out = stream(&["Authorization: B", "earer g", "hp_abcdefghijklmnopqrstuvwxyz1234567890\n"]);
    assert!(!out.contains("ghp_abcdefghijklmnopqrstuvwxyz1234567890"), "{out:?}");
}
