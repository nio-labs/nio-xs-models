use nio_mask_runtime::NioMask;

fn stream(chunks:&[&str])->String {
    let mask=NioMask::new();
    let mut out:String=chunks.iter().map(|c|mask.sanitize(c).sanitized).collect();
    out.push_str(&mask.finish().sanitized);out
}

#[test]
fn yaml_hex_escaped_sensitive_key_must_be_recognized() {
    let out=stream(&["\"\\x70assword\": AlphaSecret123!\n"]);
    assert!(!out.contains("AlphaSecret123!"),"{out:?}");
}

#[test]
fn yaml_long_unicode_sensitive_key_must_be_recognized() {
    let out=stream(&["\"\\U00000070assword\": BravoValueHidden!\n"]);
    assert!(!out.contains("BravoValueHidden!"),"{out:?}");
}

#[test]
fn numeric_json_secret_must_preserve_sibling_fields() {
    let input=r#"{"pass\u0077ord":1234567890,"name":"public"}"#;
    let original:serde_json::Value=serde_json::from_str(input).unwrap();
    assert_eq!(original["password"],1234567890u64);
    let out=stream(&[input]);
    let parsed=serde_json::from_str::<serde_json::Value>(&out);
    assert!(parsed.is_ok(),"Invalid redacted JSON: {out:?}");
    assert_eq!(parsed.unwrap()["name"],"public");
}

#[test]
fn yaml_json_style_unicode_escape_control() {
    let out=stream(&["\"\\u0070assword\": AlphaSecret123!\n"]);
    assert!(!out.contains("AlphaSecret123!"),"{out:?}");
}
