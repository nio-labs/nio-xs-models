use nio_mask_runtime::NioMask;

fn stream(chunks: &[&str]) -> String {
    let mask = NioMask::new();
    let mut out: String = chunks.iter().map(|c| mask.sanitize(c).sanitized).collect();
    out.push_str(&mask.finish().sanitized);
    out
}

#[test]
fn explicit_yaml_key_with_line_continuation_must_mask_value() {
    let input = "? \"pass\\\n  word\"\n: AlphaSecret123!\n";
    let out = stream(&[input]);
    assert!(!out.contains("AlphaSecret123!"), "{out:?}");
}

#[test]
fn json_array_under_sensitive_key_must_mask_all_elements() {
    let input = r#"{"to\u006ben":["violet","orchid"],"name":"public"}"#;
    assert_eq!(serde_json::from_str::<serde_json::Value>(input).unwrap()["token"][1], "orchid");
    let out = stream(&[input]);
    assert!(!out.contains("orchid"), "{out:?}");
}

#[test]
fn json_object_under_sensitive_key_must_remain_valid() {
    let input = r#"{"to\u006ben":{"value":"violet"},"name":"public"}"#;
    let out = stream(&[input]);
    let parsed = serde_json::from_str::<serde_json::Value>(&out);
    assert!(parsed.is_ok(), "{out:?}");
    assert_eq!(parsed.unwrap()["name"], "public");
}

#[test]
fn numeric_json_split_inside_value_must_preserve_siblings() {
    let out = stream(&[r#"{"password":123"#, r#"4567890,"name":"public"}"#]);
    let parsed = serde_json::from_str::<serde_json::Value>(&out);
    assert!(parsed.is_ok(), "{out:?}");
    assert_eq!(parsed.unwrap()["name"], "public");
}

#[test]
fn structured_values_and_yaml_keys_are_independent_of_chunk_boundaries() {
    let cases = [
        r#"{"password":1234567890,"name":"public"}"#,
        r#"{"pass\u0077ord":1234567890,"name":"public"}"#,
        r#"{"token":false,"name":"public"}"#,
        r#"{"token":null,"name":"public"}"#,
        r#"{"token":-123.456e+7,"name":"public"}"#,
        r#"{"token":["violet","orchid"],"name":"public"}"#,
        r#"{"to\u006ben":["violet","orchid"],"name":"public"}"#,
        r#"{"token":{"value":"violet"},"name":"public"}"#,
        r#"{"to\u006ben":{"value":"violet"},"name":"public"}"#,
        r#"{"to\u006ben":[{"secret":123,"value":"orchid"}],"name":"public"}"#,
        r#"{"token":{"x":["quote\"}\\",["orchid"]]},"name":"public"}"#,
        "? \"pass\\\n  word\"\n: AlphaSecret123!\n",
        "? \"pass\\\r\n  word\"\r\n: AlphaSecret123!\r\n",
    ];
    let mut errors = Vec::new();
    let mut partitions = 0;
    for input in cases {
        let expected = stream(&[input]);
        if input.starts_with('{') {
            let parsed: serde_json::Value = serde_json::from_str(&expected).unwrap();
            assert_eq!(parsed["name"], "public");
        }
        assert!(!expected.contains("orchid") && !expected.contains("violet") && !expected.contains("AlphaSecret123!"), "{expected:?}");
        for a in 0..=input.len() {
            for b in a..=input.len() {
                partitions += 1;
                let out = stream(&[&input[..a], &input[a..b], &input[b..]]);
                if out != expected && errors.len() < 12 {
                    errors.push(format!("{input:?} split={a},{b} => {out:?}, expected {expected:?}"));
                }
            }
        }
    }
    assert!(errors.is_empty(), "{}", errors.join("\n"));
    println!("Checked {partitions} three-chunk partitions");
}

#[test]
fn long_nested_json_values_are_masked_in_character_chunks() {
    let input = format!(r#"{{"token":[{{"value":"{}紫orchid"}}],"name":"public"}}"#, "x".repeat(2048));
    let chunks: Vec<&str> = input.char_indices().map(|(i, c)| &input[i..i + c.len_utf8()]).collect();
    let out = stream(&chunks);
    let parsed: serde_json::Value = serde_json::from_str(&out).unwrap();
    assert_eq!(parsed["token"], "[REDACTED_SECRET]");
    assert_eq!(parsed["name"], "public");
}

#[test]
fn finish_resets_incomplete_json_value_state() {
    for input in [r#"{"token":123"#, r#"{"token":[{"value":"orchid"#] {
        let mask = NioMask::new();
        let out = mask.sanitize(input).sanitized + &mask.finish().sanitized;
        assert!(!out.contains("123") && !out.contains("orchid"));
        let next = mask.sanitize("public text\n").sanitized + &mask.finish().sanitized;
        assert_eq!(next, "public text\n");
    }
}
