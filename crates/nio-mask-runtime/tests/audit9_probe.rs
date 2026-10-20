use nio_mask_runtime::NioMask;
fn stream(chunks:&[&str])->String{
 let m=NioMask::new();let mut out:String=chunks.iter().map(|c|m.sanitize(c).sanitized).collect();out.push_str(&m.finish().sanitized);out
}
#[test]
fn diagnostics(){
 let cases:&[(&str,&[&str])]=&[
  ("literal_hash", &["password: |\n  #AlphaSecret123!\n  BravoValueHidden!\n"]),
  ("literal_hash_stream", &["password: |\n", "  #AlphaSecret123!\n", "  BravoValueHidden!\n"]),
  ("folded_hash", &["password: >\n  #AlphaSecret123!\n  BravoValueHidden!\n"]),
  ("plain_later_comment", &["password:\n  AlphaSecret123!\n# comment\n  BravoValueHidden!\n"]),
  ("plain_later_comment_stream", &["password:\n  AlphaSecret123!\n", "# comment\n", "  BravoValueHidden!\n"]),
  ("env_bang_later", &["password=", "!Alpha", " BravoSecret123!\n"]),
  ("yaml_blank_prefix", &["password:\n", "# comment", "\n  AlphaSecret123!\n"]),
  ("yaml_explicit_hash", &["password: |2\n  #AlphaSecret123!\n  BravoValueHidden!\n"]),
  ("props_squote", &["password: ", "!!str 'Alpha'", "'BravoSecret123!'\n"]),
 ];
 for(name,chunks)in cases{println!("CASE {name} {chunks:?} -> {:?}",stream(chunks));}
}
