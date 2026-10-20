use nio_mask_runtime::NioMask;

fn stream(chunks: &[&str]) -> String {
    let m=NioMask::new();
    let mut s:String=chunks.iter().map(|c|m.sanitize(c).sanitized).collect();
    s.push_str(&m.finish().sanitized);
    s
}

#[test]
fn diagnostics() {
    let cases: &[(&str, &[&str])] = &[
        ("uri_scheme", &["post", "gres:", "//u:AlphaSecret123!@localhost/status\n"]),
        ("yaml_nested_split", &["credentials:\n  password: ", "|\n    AlphaSecret123!\n  user: public\n"]),
        ("yaml_nested_explicit", &["credentials:\n  password:", " |2\n      AlphaSecret123!\n    BravoSecret456!\n  user: public\n"]),
        ("uppercase_key", &["PASS", "WORD=AlphaSecret123!\n"]),
        ("spaced_key", &["pass", "word = AlphaSecret123!\n"]),
        ("json_spaces", &["{\"pass", "word\" : \"AlphaSecret123!\"}\n"]),
        ("unquoted_spaces", &["password=Alpha", " BravoSecret123!\n"]),
        ("prefixed_pat", &["Authorization: Bearer g", "hp_abcdefghijklmnopqrstuvwxyz1234567890\n"]),
        ("ipv4_mapped_tail", &["host=::ffff:192.0.2.", "128\n"]),
        ("yaml_header_only", &["password: | # example 9\n", "  AlphaSecret123!\n"]),
        ("yaml_comment_split", &["password:", " | # example 9\n  AlphaSecret123!\n"]),
    ];
    for (name,chunks) in cases { println!("CASE {name} {chunks:?} => {:?}",stream(chunks)); }
}

#[test]
fn expanded_matrix() {
    std::panic::set_hook(Box::new(|_|{}));
    let cases = [
        ("unquoted_spaced_value", "password=Alpha BravoSecret123!\n"),
        ("uppercase_key", "PASSWORD=AlphaSecret123!\n"),
        ("spaced_key", "password = AlphaSecret123!\n"),
        ("json_spaces", "{\"password\" : \"AlphaSecret123!\"}\n"),
        ("prefixed_pat", "Authorization: Bearer ghp_abcdefghijklmnopqrstuvwxyz1234567890\n"),
        ("uri", "postgres://u:AlphaSecret123!@localhost/status\n"),
        ("yaml_comments", "password: | # test 9\n  AlphaSecret123!\n"),
        ("yaml_nested", "credentials:\n  password: |\n    AlphaSecret123!\n  user: public\n"),
        ("yaml_explicit", "password: |2\n    AlphaSecret123!\n  BravoValueHidden!\n"),
        ("unicode", "こんにちは password=\"秘密\"\n"),
        ("pem", "-----BEGIN PRIVATE KEY-----\nAlphaSecret123!\n-----END PRIVATE KEY-----\n"),
        ("benign_log", "hello world\nuser: public\n"),
    ];
    for (name,s) in cases {
        let expected=stream(&[s]);
        let bounds:Vec<usize>=(1..s.len()).filter(|i|s.is_char_boundary(*i)).collect();
        let mut failures=0;
        let mut panics=0;
        for &a in &bounds {
            for &b in bounds.iter().filter(|b|**b>a) {
                let actual=std::panic::catch_unwind(||stream(&[&s[..a],&s[a..b],&s[b..]]));
                let actual=actual.unwrap_or_else(|_| { panics+=1; "<PANIC>".to_string() });
                if actual!=expected {
                    failures+=1;
                    if failures<=3 { println!("FAIL {name} {a} {b} {:?} => {actual:?} expected {expected:?}",[&s[..a],&s[a..b],&s[b..]]); }
                }
            }
        }
        let bytewise:Vec<&str>=s.char_indices().map(|(i,c)|&s[i..i+c.len_utf8()]).collect();
        let byte_actual=std::panic::catch_unwind(||stream(&bytewise));
        assert_eq!(failures, 0, "MATRIX {name} had {failures} failures");
        assert_eq!(panics, 0, "MATRIX {name} had {panics} panics");
        assert_eq!(byte_actual.unwrap(), expected, "MATRIX {name} bytewise failed");
    }
}
