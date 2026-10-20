use nio_mask_runtime::NioMask;
fn stream(chunks:&[&str])->String {
 let m=NioMask::new();let mut out:String=chunks.iter().map(|c|m.sanitize(c).sanitized).collect();out.push_str(&m.finish().sanitized);out
}
#[test]
fn encoded_key_matrix() {
 let mut cases=vec![
  r#"{"\u0070assword":"AlphaSecret123!"}"#.to_string(),
  r#"{"pass\u0077ord":"AlphaSecret123!"}"#.to_string(),
  r#"{"\u0070\u0061\u0073\u0073\u0077\u006f\u0072\u0064":"AlphaSecret123!"}"#.to_string(),
  "{\"pass\\u0077ord\":\n  \"AlphaSecret123!\"}\n".to_string(),
  "\"pass\\u0077ord\": !!str |\n  AlphaSecret123!\n".to_string(),
  "\"pass\\u0077ord\": !!str 'Alpha''BravoSecret123!'\n".to_string(),
 ];
 for key in ["passwd","pwd","secret","api_key","token","GITHUB_TOKEN","AWS_SECRET_ACCESS_KEY"] {
  let encoded:String=key.bytes().map(|b|format!("\\u{b:04x}")).collect();
  cases.push(format!("{{\"{encoded}\":\"AlphaSecret123!\"}}"));
 }
 let mut errors=Vec::new();let mut partitions=0;
 for input in cases {
  let expected=stream(&[&input]);
  if expected.contains("AlphaSecret123!") || expected.contains("BravoSecret123!") {errors.push(format!("BATCH LEAK {input:?} => {expected:?}"));}
  for a in 0..=input.len(){for b in a..=input.len(){
   partitions+=1;
   let actual=stream(&[&input[..a],&input[a..b],&input[b..]]);
   if actual!=expected && errors.len()<12 {errors.push(format!("{input:?} splits={a},{b} -> {actual:?} expected {expected:?}"));}
  }}
 }
 println!("Checked {partitions} encoded-key partitions");
 assert!(errors.is_empty(),"{}",errors.join("\n"));
}
#[test]
fn yaml_and_value_diagnostics() {
 for s in [
  "\"\\x70assword\": AlphaSecret123!\n",
  "\"\\U00000070assword\": BravoValueHidden!\n",
  "\"\\u0070assword\": AlphaSecret123!\n",
  r#"{"pass\u0077ord":1234567890,"name":"public"}"#,
 ] {println!("CASE {s:?} => {:?}",stream(&[s]));}
}
