use nio_mask_runtime::NioMask;
fn stream(chunks:&[&str])->String {let m=NioMask::new();let mut out:String=chunks.iter().map(|c|m.sanitize(c).sanitized).collect();out.push_str(&m.finish().sanitized);out}
#[test]
fn diagnostics(){for text in [
 "\"pass\\\n  word\": AlphaSecret123!\n",
 "\"\\x70ass\\\n  word\": AlphaSecret123!\n",
 r#"{"password":1234567890,"name":"public"}"#,
 r#"{"pass\u0077ord":1234567890,"name":"public"}"#,
 r#"{"pass\u0077ord":["AlphaSecret123!","BravoHiddenValue!"],"name":"public"}"#,
 r#"{"pass\u0077ord":{"value":"AlphaSecret123!"},"name":"public"}"#,
 r#"{"password":false,"name":"public"}"#,
 r#"{"password":null,"name":"public"}"#,
 r#"{"pass\u0077ord":-123.456e+7,"name":"public"}"#,
]{println!("{text:?} => {:?}",stream(&[text]));}}
#[test]
fn partitions(){for text in ["\"\\x70assword\": AlphaSecret123!\n","\"\\U00000070assword\": BravoValueHidden!\n",r#"{"pass\u0077ord":1234567890,"name":"public"}"#,r#"{"password":1234567890,"name":"public"}"#]{let expected=stream(&[text]);let mut count=0;for a in 0..=text.len(){for b in a..=text.len(){let out=stream(&[&text[..a],&text[a..b],&text[b..]]);if out!=expected {if count<4{println!("SPLIT {a},{b} {text:?} => {out:?} EXPECTED {expected:?}");}count+=1;}}}println!("MISMATCHES {count} INPUT {text:?}");}}
