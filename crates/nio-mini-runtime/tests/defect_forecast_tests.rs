use nio_mini_runtime::{DefectCategory, NioMini};

#[test]
fn test_clean_code_samples() {
    let mini = NioMini::new();

    let clean1 = r#"
pub fn calculate_hash(data: &[u8]) -> u64 {
    let mut hash = 5381u64;
    for &byte in data {
        hash = hash.wrapping_mul(33).wrapping_add(byte as u64);
    }
    hash
}
"#;
    let v1 = mini.forecast(clean1);
    assert!(!v1.will_break);
    assert_eq!(v1.category, DefectCategory::Clean);
    assert!(v1.risk_score < 0.10);

    let clean2 = r#"
pub struct Config {
    pub name: String,
    pub timeout_ms: u64,
}

impl Config {
    pub fn default() -> Self {
        Self { name: "default".into(), timeout_ms: 5000 }
    }
}
"#;
    let v2 = mini.forecast(clean2);
    assert!(!v2.will_break);
    assert_eq!(v2.category, DefectCategory::Clean);
}

#[test]
fn test_syntax_defects() {
    let mini = NioMini::new();

    // Unclosed brace
    let broken_brace = "pub fn foo() { let x = 1;";
    let v1 = mini.forecast(broken_brace);
    assert!(v1.will_break);
    assert_eq!(v1.category, DefectCategory::SyntaxError);

    // Mismatched delimiter
    let mismatched = "fn test(a: i32] { }";
    let v2 = mini.forecast(mismatched);
    assert!(v2.will_break);
    assert_eq!(v2.category, DefectCategory::SyntaxError);

    // Missing semicolon on let statement
    let missing_semi = "pub fn add(a: i32, b: i32) -> i32 {\n    let res = a + b\n    res\n}";
    let v3 = mini.forecast(missing_semi);
    assert!(v3.will_break);
    assert_eq!(v3.category, DefectCategory::SyntaxError);
}

#[test]
fn test_borrow_checker_defects() {
    let mini = NioMini::new();

    let double_mut = r#"
pub fn bad_borrow(data: &mut Vec<i32>) {
    let a = &mut data;
    let b = &mut data;
}
"#;
    let v1 = mini.forecast(double_mut);
    assert!(v1.will_break);
    assert_eq!(v1.category, DefectCategory::BorrowCheckFail);

    let compiler_err = "error[E0499]: cannot borrow `*data` as mutable more than once at a time";
    let v2 = mini.forecast(compiler_err);
    assert!(v2.will_break);
    assert_eq!(v2.category, DefectCategory::BorrowCheckFail);
}

#[test]
fn test_type_mismatch_defects() {
    let mini = NioMini::new();

    let wrong_return = r#"
pub fn get_count() -> u64 {
    return -1;
}
"#;
    let v1 = mini.forecast(wrong_return);
    assert!(v1.will_break);
    assert_eq!(v1.category, DefectCategory::TypeMismatch);

    let compiler_err = "error[E0308]: mismatched types: expected `String`, found `i32`";
    let v2 = mini.forecast(compiler_err);
    assert!(v2.will_break);
    assert_eq!(v2.category, DefectCategory::TypeMismatch);
}

#[test]
fn test_regression_defects() {
    let mini = NioMini::new();

    let failing_assert = r#"
#[test]
fn test_invariants() {
    assert!(false);
}
"#;
    let v1 = mini.forecast(failing_assert);
    assert!(v1.will_break);
    assert_eq!(v1.category, DefectCategory::TestRegression);

    let suite_failure = "test result: FAILED. 1 passed; 1 failed;";
    let v2 = mini.forecast(suite_failure);
    assert!(v2.will_break);
    assert_eq!(v2.category, DefectCategory::TestRegression);
}
