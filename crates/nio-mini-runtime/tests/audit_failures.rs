use nio_mini_runtime::{DefectCategory, NioMini};

#[test]
fn actual_syntax_error_is_not_clean() {
    let v = NioMini::new().forecast("fn main() { let x = ; }");
    assert!(v.will_break, "{v:?}");
    assert_eq!(v.category, DefectCategory::SyntaxError);
}

#[test]
fn actual_type_error_is_not_clean() {
    let v = NioMini::new().forecast("fn main() { let x: u32 = \"text\"; }");
    assert!(v.will_break, "{v:?}");
    assert_eq!(v.category, DefectCategory::TypeMismatch);
}

#[test]
fn actual_borrow_error_is_not_clean() {
    let v = NioMini::new().forecast("fn main() { let mut x = 0; let a = &mut x; let b = &mut x; println!(\"{} {}\", a, b); }");
    assert!(v.will_break, "{v:?}");
    assert_eq!(v.category, DefectCategory::BorrowCheckFail);
}

#[test]
fn valid_empty_statements_are_clean() {
    let v = NioMini::new().forecast("fn main() { ;; }");
    assert!(!v.will_break, "{v:?}");
    assert_eq!(v.category, DefectCategory::Clean);
}

#[test]
fn comments_do_not_induce_type_errors() {
    let v = NioMini::new().forecast("fn main() { /* mismatched types */ }");
    assert!(!v.will_break, "{v:?}");
    assert_eq!(v.category, DefectCategory::Clean);
}
