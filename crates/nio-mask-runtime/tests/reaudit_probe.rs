use nio_mask_runtime::NioMask;

fn stream(chunks: &[&str]) -> String {
    let m=NioMask::new();
    let mut out:String=chunks.iter().map(|s|m.sanitize(s).sanitized).collect();
    out.push_str(&m.finish().sanitized);
    out
}

#[test]
fn diagnostics() {
    let cases: &[(&str,&[&str])] = &[
        ("yaml_partial", &["password: |\n  Alpha", " BravoSecret123!\n"]),
        ("yaml_sequence", &["- password: |\n    AlphaSecret123!\n"]),
        ("yaml_flow", &["credentials: {password: |\n  AlphaSecret123!\n}"]),
        ("standalone_onechar", &["g", "hp_abcdefghijklmnopqrstuvwxyz1234567890\n"]),
        ("finish_quoted", &["password=\"", "AlphaSecret123!"]),
        ("finish_single", &["password='", "AlphaSecret123!'"]),
        ("finish_stitched", &["pass", "word=\"AlphaSecret123!"]),
        ("yaml_header_split", &["password:", " |\n  AlphaSecret123!\n"]),
        ("json_split_key", &["{\"pass", "word\":\"AlphaSecret123!\"}\n"]),
        ("yaml_quoted_multiline", &["password: \"AlphaSecret123!\n  BravoSecret456!\"\n"]),
        ("awaiting_quoted_multiline", &["password=", "\"AlphaSecret123!\n  BravoSecret456!\"\n"]),
        ("ip_three", &["host=192.168.1.1", "0", "0\n"]),
    ];
    for (name,chunks) in cases { println!("CASE {name} {chunks:?} => {:?}",stream(chunks)); }
    for input in ["\"=", "':", "\":", "'=", "hello '\u{3a}"] {
        println!("PANIC {input:?} => {:?}",std::panic::catch_unwind(||stream(&[input])));
    }
}

#[test]
fn split_matrix() {
    std::panic::set_hook(Box::new(|_|{}));
    let cases = [
        ("yaml", "password: |\n  AlphaSecret123!\n  BravoSecret456!\n"),
        ("yaml_nested", "credentials:\n  password: |\n    AlphaSecret123!\n  user: public\n"),
        ("yaml_multiline_spaces", "password: |\n  Alpha BravoSecret123!\n"),
        ("json", "{\"password\":\"AlphaSecret123!\"}\n"),
        ("quoted", "password=\"Alpha BravoSecret123!\"\n"),
        ("pat", "ghp_abcdefghijklmnopqrstuvwxyz1234567890\n"),
        ("uri", "postgres://u:AlphaSecret123!@localhost/status\n"),
        ("email", "contact alice@example.com\n"),
        ("ipv4", "host=192.168.1.100\n"),
        ("ipv6", "host=2001:db8::1234\n"),
    ];
    for (name,s) in cases {
        let expected=stream(&[s]);
        let mut failures=0;
        for a in 1..s.len() {
            if !s.is_char_boundary(a) { continue; }
            for b in a+1..s.len() {
                if !s.is_char_boundary(b) { continue; }
                let outcome=std::panic::catch_unwind(||stream(&[&s[..a],&s[a..b],&s[b..]]));
                let actual=outcome.unwrap_or_else(|_| "<PANIC>".to_string());
                if actual!=expected {
                    failures+=1;
                    if failures<=4 { println!("FAIL {name} {a} {b} {:?} => {actual:?} expected {expected:?}",[&s[..a],&s[a..b],&s[b..]]); }
                }
            }
        }
        assert_eq!(failures, 0, "MATRIX {name} had {failures} failures");
    }
}
