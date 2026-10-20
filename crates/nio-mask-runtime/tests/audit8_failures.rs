use nio_mask_runtime::NioMask;

fn stream(chunks: &[&str]) -> String {
    let mask = NioMask::new();
    let mut out: String = chunks.iter().map(|c| mask.sanitize(c).sanitized).collect();
    out.push_str(&mask.finish().sanitized);
    out
}

#[test]
fn env_bang_value_after_key_must_be_hidden() {
    let out = stream(&["password=", "!AlphaSecret123!\n"]);
    assert!(!out.contains("!AlphaSecret123!"), "{out:?}");
}

#[test]
fn env_ampersand_value_after_key_must_be_hidden() {
    let out = stream(&["password=", "&AlphaSecret123!\n"]);
    assert!(!out.contains("&AlphaSecret123!"), "{out:?}");
}

#[test]
fn env_value_prefix_is_not_a_yaml_property() {
    let out = stream(&["password=", "!Alpha BravoSecret123!\n"]);
    assert!(!out.contains("!Alpha"), "{out:?}");
}

#[test]
fn tagged_single_quote_must_defer_ambiguous_final_quote() {
    let out = stream(&["password: ", "!!str 'Alpha'", "'BravoSecret123!'\n"]);
    assert!(!out.contains("BravoSecret123!"), "{out:?}");
}

#[test]
fn yaml_comment_before_scalar_must_not_disable_redaction() {
    let out = stream(&["password:\n# comment\n  AlphaSecret123!\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn streamed_yaml_comment_before_scalar_must_not_end_secret() {
    let out = stream(&["password:\n", "# comment\n", "  AlphaSecret123!\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn quoted_env_value_control() {
    assert_eq!(stream(&["password=", "\"!AlphaSecret123!\"\n"]), "password=\"[REDACTED_SECRET]\"\n");
}
