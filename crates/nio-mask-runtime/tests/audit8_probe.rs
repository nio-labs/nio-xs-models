use nio_mask_runtime::NioMask;
fn stream(chunks:&[&str])->String {
 let m=NioMask::new();let mut out:String=chunks.iter().map(|c|m.sanitize(c).sanitized).collect();out.push_str(&m.finish().sanitized);out
}
#[test]
fn diagnostics() {
 let cases:&[(&str,&[&str])]=&[
  ("env_bang_split", &["password=", "!AlphaSecret123!\n"]),
  ("env_amp_split", &["password=", "&AlphaSecret123!\n"]),
  ("env_bang_spaces", &["password=", "!Alpha BravoSecret123!\n"]),
  ("yaml_tag_squote_boundary", &["password: ", "!!str 'Alpha'", "'BravoSecret123!'\n"]),
  ("yaml_tag_escape", &["password: ", "!!str \"Alpha\\", "\"BravoSecret123!\"\n"]),
  ("yaml_comment", &["password:\n# comment\n  AlphaSecret123!\n"]),
  ("yaml_comments", &["password:\n# first\n# second\n  AlphaSecret123!\n"]),
  ("yaml_null_then_comment", &["password:\n# comment\nname: public\n"]),
  ("spaces_before_quote", &["password=", " ", "\"AlphaSecret123!\"\n"]),
  ("spaces_with_quote", &["password=", " \"Alpha", " BravoSecret123!\"\n"]),
  ("yaml_comments_stream", &["password:\n", "# comment\n", "  AlphaSecret123!\n"]),
 ];
 for (name,chunks) in cases {println!("CASE {name} {chunks:?} -> {:?}",stream(chunks));}
}

#[test]
fn matrices() {
 let cases=[
  ("env_bang", "password=!AlphaSecret123!\n"),
  ("env_amp", "password=&AlphaSecret123!\n"),
  ("yaml_tag_squote", "password: !!str 'Alpha''BravoSecret123!'\n"),
  ("yaml_tag_dquote", "password: !!str \"Alpha\\\"BravoSecret123!\"\n"),
  ("json_pretty", "{\n  \"password\":\n    \"AlphaSecret123!\",\n  \"name\": \"public\"\n}\n"),
  ("following_line", "password:\n  AlphaSecret123!\n"),
  ("yaml_comment", "password:\n# comment\n  AlphaSecret123!\n"),
 ];
 for (name,s) in cases {
  let expected=stream(&[s]);let mut failed=0;
  for a in 1..s.len(){for b in a+1..s.len(){
   let chunks=[&s[..a],&s[a..b],&s[b..]];
   let actual=stream(&chunks);
   if actual!=expected {failed+=1;if failed<=3{println!("FAIL {name} {chunks:?} -> {actual:?}; expected={expected:?}");}}
  }}
  println!("MATRIX {name} failures={failed}");
 }
}
