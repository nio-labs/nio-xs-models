use nio_mask_runtime::NioMask;

fn stream(chunks: &[&str]) -> String {
    let m=NioMask::new(); let mut out:String=chunks.iter().map(|c|m.sanitize(c).sanitized).collect();
    out.push_str(&m.finish().sanitized); out
}

#[test]
fn scalar_style_chunk_boundaries() {
    let cases=[
        "password: |\n  #AlphaSecret123!\n  BravoValueHidden!\n",
        "password: >\n  #AlphaSecret123!\n  BravoValueHidden!\n",
        "password: |2\n  #AlphaSecret123!\n  BravoValueHidden!\n",
        "password: |-\n\n  #AlphaSecret123!\n  BravoValueHidden!\n",
        "password: !!str |\r\n  #AlphaSecret123!\r\n  BravoValueHidden!\r\n",
        "credentials:\n  password: |\n    #AlphaSecret123!\n    BravoValueHidden!\n  name: public\n",
        "password:\n# first\n# second\n  AlphaSecret123!\n",
        "password:\n# comment\n  Alpha#BravoValueHidden!\n",
        "password: \"Alpha#BravoValueHidden!\"\n",
        "password='Alpha#BravoValueHidden!'\n",
        "password: |\n  #秘密\n  สวัสดี\n",
    ];
    let mut mismatches=Vec::new(); let mut partitions=0;
    for s in cases {
        let expected=stream(&[s]);
        let bounds:Vec<usize>=(0..=s.len()).filter(|i|s.is_char_boundary(*i)).collect();
        for (ai,&a) in bounds.iter().enumerate() { for &b in &bounds[ai..] {
            partitions+=1;
            let actual=stream(&[&s[..a],&s[a..b],&s[b..]]);
            if actual!=expected && mismatches.len()<10 { mismatches.push(format!("{s:?} splits {a},{b}: {actual:?} expected {expected:?}")); }
        }}
    }
    println!("Checked {partitions} three-chunk partitions, including empty chunks");
    assert!(mismatches.is_empty(), "{}", mismatches.join("\n"));
}
