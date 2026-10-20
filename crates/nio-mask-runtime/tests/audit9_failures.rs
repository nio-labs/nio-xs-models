use nio_mask_runtime::NioMask;

fn stream(chunks: &[&str]) -> String {
    let mask = NioMask::new();
    let mut out: String = chunks.iter().map(|c| mask.sanitize(c).sanitized).collect();
    out.push_str(&mask.finish().sanitized);
    out
}

#[test]
fn literal_scalar_hash_line_is_secret_content() {
    let out = stream(&["password: |\n  #AlphaSecret123!\n  BravoValueHidden!\n"]);
    assert!(!out.contains("#AlphaSecret123!"), "{out:?}");
}

#[test]
fn folded_scalar_hash_line_is_secret_content() {
    let out = stream(&["password: >\n  #AlphaSecret123!\n  BravoValueHidden!\n"]);
    assert!(!out.contains("#AlphaSecret123!"), "{out:?}");
}

#[test]
fn streamed_literal_scalar_hash_line_is_secret_content() {
    let out = stream(&["password: |\n", "  #AlphaSecret123!\n", "  BravoValueHidden!\n"]);
    assert!(!out.contains("#AlphaSecret123!"), "{out:?}");
}

#[test]
fn explicit_indent_literal_control() {
    let out = stream(&["password: |2\n  #AlphaSecret123!\n  BravoValueHidden!\n"]);
    assert!(!out.contains("#AlphaSecret123!"), "{out:?}");
}
