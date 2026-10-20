use nio_mask_runtime::NioMask;
#[test]
fn redacts_ipv4() { assert!(!NioMask::new().sanitize("host=192.168.1.100").sanitized.contains("192.168.1.100")); }
#[test]
fn redacts_password() { assert!(!NioMask::new().sanitize("password=SuperSecretPass123!").sanitized.contains("SuperSecretPass123!")); }
#[test]
fn redacts_private_key_body() { assert!(!NioMask::new().sanitize("-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEAAbCdEfGhIjKlMnOp\n-----END RSA PRIVATE KEY-----").sanitized.contains("MIIEowIBAAKCAQEAAbCdEfGhIjKlMnOp")); }
#[test]
fn safe_unicode_before_email() { assert!(NioMask::new().sanitize("สวัสดี\u{2003}alice@example.com").sanitized.contains("[REDACTED_PII]")); }
#[test]
fn offsets_reference_original() { let text="ghp_abcdefghijklmnopqrstuvwxyz1234567890 alice@example.com"; let r=NioMask::new().sanitize(text); let email=r.spans.iter().find(|s| s.category=="PII_EMAIL").unwrap(); assert_eq!(&text[email.start..email.end], "alice@example.com"); }
#[test]
fn serialized_output_does_not_leak_original() { let r=NioMask::new().sanitize("token=ghp_abcdefghijklmnopqrstuvwxyz1234567890"); assert!(!serde_json::to_string(&r).unwrap().contains("ghp_abcdefghijklmnopqrstuvwxyz1234567890")); }
#[test]
fn chunk_boundary_secret() { let m=NioMask::new(); let clean=format!("{}{}",m.sanitize("token=gh").sanitized,m.sanitize("p_abcdefghijklmnopqrstuvwxyz1234567890").sanitized); assert!(!clean.contains("ghp_abcdefghijklmnopqrstuvwxyz1234567890")); }
#[test]
fn redacts_known_pat() { assert!(NioMask::new().sanitize("token=ghp_abcdefghijklmnopqrstuvwxyz1234567890").sanitized.contains("[REDACTED_SECRET]")); }
