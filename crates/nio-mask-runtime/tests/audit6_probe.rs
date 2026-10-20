use nio_mask_runtime::NioMask;
fn stream(chunks: &[&str]) -> String {
 let m=NioMask::new(); let mut out:String=chunks.iter().map(|c|m.sanitize(c).sanitized).collect(); out.push_str(&m.finish().sanitized); out
}
#[test]
fn diagnostics() {
 let cases: &[(&str, &[&str])] = &[
  ("bang_password", &["password=!AlphaSecret123!\n"]),
  ("amp_password", &["password=&AlphaSecret123!\n"]),
  ("bang_with_spaces", &["password=!Alpha BravoSecret123!\n"]),
  ("hello_g", &["hello g", "hp_abcdefghijklmnopqrstuvwxyz1234567890\n"]),
  ("hello_stripe", &["hello s", "k_live_abcdefghijklmnopqrstuvwxyz123456\n"]),
  ("yaml_eof_bang", &["password: !AlphaSecret123!\n"]),
  ("yaml_tag_empty", &["password: !!str\n  AlphaSecret123!\n"]),
  ("yaml_tagquoted", &["password: !!str \"AlphaSecret123!\"\n"]),
  ("yaml_tagquoted_split", &["password: !!str \"Alpha", " BravoSecret123!\"\n"]),
  ("onechar_uri", &["x", ":", "//u:AlphaSecret123!@localhost/path\n"]),
  ("json_emptyline", &["{\"password\":\n\n", " \"AlphaSecret123!\"}\n"]),
  ("yaml_tag_newline", &["password: !!str\n  AlphaSecret123!\n"]),
  ("pem_crlf_split", &["-----BEGIN PRIVATE KEY-----\r", "\nAlphaSecret123!\n-----END PRIVATE KEY-----\n"]),
 ];
 for (name,chunks) in cases { println!("CASE {name} {chunks:?} -> {:?}",stream(chunks)); }
}

#[test]
fn matrices() {
 let cases=[
  ("yaml_tagged_quote", "password: !!str \"Alpha BravoSecret123!\"\n"),
  ("yaml_tagged_inline", "password: !!str AlphaSecret123!\n"),
  ("yaml_anchor_inline", "password: &credential AlphaSecret123!\n"),
  ("yaml_tag_noindicator", "password: !!str\n  AlphaSecret123!\n"),
  ("json_pretty", "{\"password\":\n  \"AlphaSecret123!\"}\n"),
  ("hello_pat", "hello ghp_abcdefghijklmnopqrstuvwxyz1234567890\n"),
  ("hello_stripe", "hello sk_live_abcdefghijklmnopqrstuvwxyz123456\n"),
  ("onechar_uri", "x://u:AlphaSecret123!@localhost/path\n"),
 ];
 for (name,s) in cases {
  let expected=stream(&[s]); let mut fails=0;
  for a in 1..s.len() { for b in a+1..s.len() {
   let chunks=[&s[..a],&s[a..b],&s[b..]];
   let actual=stream(&chunks);
   if actual!=expected { fails+=1; if fails<=3 { println!("FAIL {name} {chunks:?} -> {actual:?}; expected={expected:?}"); } }
  }}
  println!("MATRIX {name} failures={fails}");
 }
}
