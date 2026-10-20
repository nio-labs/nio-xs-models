use nio_mask_runtime::NioMask;
#[test] fn stream_complete_prefix_split() { let m=NioMask::new(); let s=format!("{}{}",m.sanitize("token=ghp_").sanitized,m.sanitize("abcdefghijklmnopqrstuvwxyz1234567890").sanitized); assert!(!s.contains("ghp_abcdefghijklmnopqrstuvwxyz1234567890"),"{s}"); }
#[test] fn stream_payload_tail() { let m=NioMask::new(); let s=format!("{}{}",m.sanitize("token=ghp_abcdefghijklmnop").sanitized,m.sanitize("qrstuvwxyz1234567890").sanitized); assert!(!s.contains("qrstuvwxyz1234567890"),"{s}"); }
#[test] fn stream_private_key_body() { let m=NioMask::new(); let s=format!("{}{}",m.sanitize("-----BEGIN RSA PRIVATE KEY-----\n").sanitized,m.sanitize("MIIEowIBAAKCAQEAAbCdEfGhIjKlMnOp\n-----END RSA PRIVATE KEY-----\n").sanitized); assert!(!s.contains("MIIEowIBAAKCAQEAAbCdEfGhIjKlMnOp"),"{s}"); }
#[test] fn stream_email_split() { let m=NioMask::new(); let s=format!("{}{}",m.sanitize("contact alice@").sanitized,m.sanitize("example.com\n").sanitized); assert!(!s.contains("alice@example.com"),"{s}"); }
#[test] fn stream_password_split() { let m=NioMask::new(); let s=format!("{}{}",m.sanitize("password=").sanitized,m.sanitize("SuperSecretPass123!\n").sanitized); assert!(!s.contains("SuperSecretPass123!"),"{s}"); }
#[test] fn preserves_final_benign_prefix() { let m = NioMask::new(); let mut s = m.sanitize("hello g").sanitized; s.push_str(&m.finish().sanitized); assert_eq!(s, "hello g"); }
#[test] fn quoted_password() { let s=NioMask::new().sanitize("password=\"SuperSecretPass123!\"").sanitized; assert!(!s.contains("SuperSecretPass123!"),"{s}"); }
#[test] fn unicode_lowercase_offsets() { let s=NioMask::new().sanitize("İ password=秘密密码").sanitized; assert!(!s.contains("秘密密码"),"{s}"); }
#[test] fn unicode_lowercase_ascii_password() { let s=NioMask::new().sanitize("İ password=SuperSecretPass123!").sanitized; assert!(!s.contains("password=S"),"{s}"); }
#[test] fn all_uri_credentials() { let s=NioMask::new().sanitize("postgres://u:FirstPass123@localhost postgres://u:SecondPass456@localhost").sanitized; assert!(!s.contains("SecondPass456"),"{s}"); }
#[test] fn ipv6() { let s=NioMask::new().sanitize("host=2001:db8::1").sanitized; assert!(!s.contains("2001:db8::1"),"{s}"); }
#[test] fn preserves_public_certificate() { let text="-----BEGIN CERTIFICATE-----\nPUBLICDATA\n-----END CERTIFICATE-----"; assert_eq!(NioMask::new().sanitize(text).sanitized,text); }
#[test] fn ipv4_sentence_punctuation() { let s=NioMask::new().sanitize("Connecting to 192.168.1.100.").sanitized; assert!(!s.contains("192.168.1.100"),"{s}"); }
#[test] fn quoted_short_password_control() { assert!(NioMask::new().sanitize("password=Ab12Cd34").sanitized.contains("[REDACTED_SECRET]")); }
