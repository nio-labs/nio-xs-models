use nio_mask_runtime::NioMask;

fn stream(chunks: &[&str]) -> String {
    let m=NioMask::new();
    let mut out:String=chunks.iter().map(|c|m.sanitize(c).sanitized).collect();
    out.push_str(&m.finish().sanitized); out
}

#[test]
fn escaped_character_inside_sensitive_key_must_be_recognized() {
    let input=r#"{"pass\u0077ord":"AlphaSecret123!"}"#;
    let value:serde_json::Value=serde_json::from_str(input).unwrap();
    assert_eq!(value["password"], "AlphaSecret123!");
    let out=stream(&[input]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn escaped_first_character_of_sensitive_key_must_be_recognized() {
    let input=r#"{"\u0070assword":"BravoValueHidden!"}"#;
    let value:serde_json::Value=serde_json::from_str(input).unwrap();
    assert_eq!(value["password"], "BravoValueHidden!");
    let out=stream(&[input]);
    assert!(!out.contains("BravoValueHidden!"), "{out:?}");
}

#[test]
fn split_escaped_sensitive_key_must_not_expose_password() {
    let out=stream(&[r#"{"pass\u00"#,r#"77ord":"AlphaSecret123!"}"#]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn ordinary_sensitive_key_control() {
    let out=stream(&[r#"{"password":"AlphaSecret123!"}"#]);
    assert_eq!(out,r#"{"password":"[REDACTED_SECRET]"}"#);
}
