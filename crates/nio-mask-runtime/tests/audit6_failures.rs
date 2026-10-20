use nio_mask_runtime::NioMask;

fn stream(chunks: &[&str]) -> String {
    let mask = NioMask::new();
    let mut out: String = chunks.iter().map(|c| mask.sanitize(c).sanitized).collect();
    out.push_str(&mask.finish().sanitized);
    out
}

#[test]
fn bang_prefixed_env_password_must_be_hidden() {
    let out = stream(&["password=!AlphaSecret123!\n"]);
    assert!(!out.contains("!AlphaSecret123!"), "{out:?}");
}

#[test]
fn ampersand_prefixed_env_password_must_be_hidden() {
    let out = stream(&["password=&AlphaSecret123!\n"]);
    assert!(!out.contains("&AlphaSecret123!"), "{out:?}");
}

#[test]
fn yaml_tagged_plain_value_on_next_line_must_be_hidden() {
    let out = stream(&["password: !!str\n  AlphaSecret123!\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn ordinary_yaml_value_on_next_line_must_be_hidden() {
    let out = stream(&["password:\n  BravoValueHidden!\n"]);
    assert!(!out.contains("BravoValueHidden!"), "{out:?}");
}

#[test]
fn hello_does_not_make_a_stripe_key_safe() {
    let out = stream(&["hello s", "k_live_abcdefghijklmnopqrstuvwxyz123456\n"]);
    assert!(!out.contains("sk_live_abcdefghijklmnopqrstuvwxyz123456"), "{out:?}");
}

#[test]
fn hello_does_not_allow_a_token_prefix_to_escape() {
    let out = stream(&["hello g", "hp_abcdefghijklmnopqrstuvwxyz1234567890\n"]);
    assert_eq!(out, "hello [REDACTED_SECRET]\n");
}

#[test]
fn one_character_uri_scheme_must_not_expose_password() {
    let out = stream(&["x", ":", "//u:AlphaSecret123!@localhost/path\n"]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn quoted_bang_prefixed_password_control() {
    assert_eq!(stream(&["password=\"!AlphaSecret123!\"\n"]), "password=\"[REDACTED_SECRET]\"\n");
}
