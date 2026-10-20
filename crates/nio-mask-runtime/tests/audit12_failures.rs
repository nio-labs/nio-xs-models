use nio_mask_runtime::NioMask;
fn stream(chunks:&[&str])->String {let m=NioMask::new();let mut out:String=chunks.iter().map(|c|m.sanitize(c).sanitized).collect();out.push_str(&m.finish().sanitized);out}
#[test]
fn explicit_yaml_key_with_line_continuation_must_mask_value(){
 let input="? \"pass\\\n  word\"\n: AlphaSecret123!\n";
 let out=stream(&[input]);assert!(!out.contains("AlphaSecret123!"),"{out:?}");
}
#[test]
fn json_array_under_sensitive_key_must_mask_all_elements(){
 let input=r#"{"to\u006ben":["violet","orchid"],"name":"public"}"#;
 assert_eq!(serde_json::from_str::<serde_json::Value>(input).unwrap()["token"][1],"orchid");
 let out=stream(&[input]);assert!(!out.contains("orchid"),"{out:?}");
}
#[test]
fn json_object_under_sensitive_key_must_remain_valid(){
 let input=r#"{"to\u006ben":{"value":"violet"},"name":"public"}"#;
 let out=stream(&[input]);let parsed=serde_json::from_str::<serde_json::Value>(&out);
 assert!(parsed.is_ok(),"{out:?}");assert_eq!(parsed.unwrap()["name"],"public");
}
#[test]
fn numeric_json_split_inside_value_must_preserve_siblings(){
 let out=stream(&[r#"{"password":123"#,r#"4567890,"name":"public"}"#]);
 let parsed=serde_json::from_str::<serde_json::Value>(&out);
 assert!(parsed.is_ok(),"{out:?}");assert_eq!(parsed.unwrap()["name"],"public");
}
