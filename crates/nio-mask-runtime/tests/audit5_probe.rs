use nio_mask_runtime::NioMask;
fn stream(chunks: &[&str]) -> String {
 let m=NioMask::new();
 let mut out:String=chunks.iter().map(|c|m.sanitize(c).sanitized).collect();
 out.push_str(&m.finish().sanitized); out
}
#[test]
fn diagnostics() {
 let longkey=format!("password{}", " ".repeat(48));
 let cases:Vec<(&str,Vec<&str>)>=vec![
  ("history_limit",vec![&longkey,"=AlphaSecret123!\n"]),
  ("custom_uri",vec!["ft", "p://u:AlphaSecret123!@localhost/path\n"]),
  ("bearer_four",vec!["Authorization: B","e","arer g","hp_abcdefghijklmnopqrstuvwxyz1234567890\n"]),
  ("general_prefix",vec!["value g","hp_abcdefghijklmnopqrstuvwxyz1234567890\n"]),
  ("yaml_tag_split",vec!["password: !!s","tr |\n  AlphaSecret123!\n"]),
  ("yaml_tag_after_key",vec!["password:", " !!str |\n  AlphaSecret123!\n"]),
  ("json_linebreak",vec!["{\"password\"", "\n: \"AlphaSecret123!\"}\n"]),
  ("password_crlf",vec!["password=Alpha\r", "\npublic\n"]),
  ("yaml_comment_pipes",vec!["password: | # a > b\n  Alpha", "Secret123!\n"]),
  ("json_key_newline",vec!["{\"pass", "word\"\n: \"AlphaSecret123!\"}\n"]),
 ];
 for (name,chunks) in cases { println!("CASE {name}: {:?} -> {:?}",chunks,stream(&chunks)); }
}

#[test]
fn matrix() {
 let cases=[
  ("yaml_tag", "password: !!str |\n  AlphaSecret123!\n"),
  ("yaml_anchor", "password: &credential |\n  AlphaSecret123!\n"),
  ("yaml_crlf", "password: |\r\n  AlphaSecret123!\r\n"),
  ("json_crlf", "{\"password\":\r\n \"AlphaSecret123!\"}\r\n"),
  ("json_tab", "{\"password\"\t:\t\"AlphaSecret123!\"}\n"),
  ("json_multiline", "{\"password\"\n: \"AlphaSecret123!\"}\n"),
  ("yaml_squote", "password: 'Alpha''BravoSecret123!'\n"),
  ("json_escape", "{\"password\":\"Alpha\\\"BravoSecret123!\"}\n"),
  ("yaml_blank", "password: |\n  AlphaSecret123!\n\n  BravoSecret456!\n"),
  ("prefixed_pat", "value ghp_abcdefghijklmnopqrstuvwxyz1234567890\n"),
  ("uri_custom", "ftp://u:AlphaSecret123!@localhost/path\n"),
 ];
 for (name,s) in cases {
  let expected=stream(&[s]); let mut failed=0; let mut empty_failed=0;
  for a in 1..s.len() {
   for b in a+1..s.len() {
    let chunks=[&s[..a],&s[a..b],&s[b..]];
    let actual=stream(&chunks);
    if actual!=expected { failed+=1; if failed<=2 { println!("FAIL {name} {chunks:?} => {actual:?}; expected {expected:?}"); } }
    let empty=[&s[..a],"",&s[a..b],"",&s[b..]];
    let actual_empty=stream(&empty);
    if actual_empty!=expected { empty_failed+=1; if empty_failed<=2 { println!("EMPTY FAIL {name} {empty:?} => {actual_empty:?}"); } }
   }
  }
  println!("MATRIX {name} failures={failed}, with_empty={empty_failed}");
 }
}
