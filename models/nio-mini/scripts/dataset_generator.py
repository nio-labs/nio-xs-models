"""
NioMini Synthetic & Structural AST Diff Dataset Generator
Generates realistic code samples across 5 defect categories:
  0: CLEAN
  1: SYNTAX_ERROR
  2: TYPE_MISMATCH
  3: BORROW_CHECK_FAIL
  4: TEST_REGRESSION

Extracts token_ids and a 32-dimensional AST feature tensor for each sample.
"""

import random
import re
from typing import Dict, List, Tuple
import numpy as np

VOCAB_SIZE = 8192
MAX_SEQ_LEN = 128
AST_FEATURE_DIM = 32

LABELS = [
    "CLEAN",
    "SYNTAX_ERROR",
    "TYPE_MISMATCH",
    "BORROW_CHECK_FAIL",
    "TEST_REGRESSION"
]

# --- 1. Code Templates & Synthesizers ---

CLEAN_TEMPLATES = [
    """pub fn calculate_hash(data: &[u8]) -> u64 {
    let mut hash = 5381u64;
    for &byte in data {
        hash = hash.wrapping_mul(33).wrapping_add(byte as u64);
    }
    hash
}""",
    """pub struct Config {
    pub name: String,
    pub timeout_ms: u64,
    pub retries: u32,
}

impl Config {
    pub fn default() -> Self {
        Self { name: "default".into(), timeout_ms: 5000, retries: 3 }
    }
}""",
    """pub fn process_items<T: std::fmt::Display>(items: &[T]) -> usize {
    let mut count = 0;
    for item in items {
        count += 1;
    }
    count
}""",
    """pub fn find_entry(records: &[(String, u32)], target: &str) -> Option<u32> {
    records.iter().find(|(k, _)| k == target).map(|(_, v)| *v)
}""",
    """pub async fn fetch_status(client: &reqwest::Client, url: &str) -> Result<u16, reqwest::Error> {
    let resp = client.get(url).send().await?;
    Ok(resp.status().as_u16())
}""",
    """pub fn sanitize_buffer(buf: &mut [u8]) {
    for b in buf.iter_mut() {
        if *b < 32 { *b = b' '; }
    }
}""",
    """pub fn parse_pair(s: &str) -> Result<(i32, i32), std::num::ParseIntError> {
    let mut parts = s.split(',');
    let a = parts.next().unwrap_or("0").trim().parse::<i32>()?;
    let b = parts.next().unwrap_or("0").trim().parse::<i32>()?;
    Ok((a, b))
}"""
]

SYNTAX_ERROR_TEMPLATES = [
    """pub fn compute_sum(a: i32, b: i32) -> i32 {
    let result = a + b
    result
}""",
    """pub struct Worker {
    pub id: u32,
    pub active: bool
}

impl Worker {
    pub fn new(id: u32) -> Self {
        Self { id, active: true }
    }
""",
    """pub fn get_names(map: &HashMap<String, u32>) -> Vec<String> {
    let mut names = Vec::new();
    for (k, _) in map {
        names.push(k.clone());
    return names;
}""",
    """pub fn validate_range(val: u32, min: u32, max: u32) -> bool {
    if (val >= min && val <= max {
        true
    } else {
        false
    }
}""",
    """pub fn parse_input(raw: &str) -> Option<i32> {
    raw.trim().parse::<i32>().ok(
}"""
]

TYPE_MISMATCH_TEMPLATES = [
    """pub fn get_user_id() -> u64 {
    let id_str: &str = "104928";
    id_str
}""",
    """pub fn sum_lengths(a: &str, b: &str) -> i32 {
    let total: usize = a.len() + b.len();
    total
}""",
    """pub fn is_authorized(role: &str) -> bool {
    if role == "admin" {
        1
    } else {
        0
    }
}""",
    """pub fn parse_record(val: Option<u32>) -> u32 {
    match val {
        Some(v) => v,
        None => "missing",
    }
}""",
    """pub fn build_url(domain: String, path: &str) -> String {
    let combined = domain + path;
    combined.len()
}"""
]

BORROW_CHECK_FAIL_TEMPLATES = [
    """pub fn mutate_twice(list: &mut Vec<i32>) {
    let r1 = &mut *list;
    let r2 = &mut *list;
    r1.push(1);
    r2.push(2);
}""",
    """pub fn pop_and_read(data: &mut Vec<String>) -> Option<&String> {
    let first = data.first();
    data.clear();
    first
}""",
    """pub fn transfer_ownership(s: String) -> String {
    let a = s;
    let b = s;
    format!("{} - {}", a, b)
}""",
    """pub fn invalid_return_ref() -> &str {
    let local = String::from("temporary string");
    local.as_str()
}""",
    """pub fn modify_in_loop(items: &mut Vec<i32>) {
    for item in items.iter() {
        if *item > 10 {
            items.push(0);
        }
    }
}"""
]

TEST_REGRESSION_TEMPLATES = [
    """#[test]
fn test_divide_positive() {
    let result = 100 / 0;
    assert_eq!(result, 100);
}""",
    """#[test]
fn test_array_bounds() {
    let v = vec![1, 2, 3];
    assert_eq!(v[99], 1);
}""",
    """#[test]
fn test_empty_string_unwrapping() {
    let opt: Option<&str> = None;
    assert_eq!(opt.unwrap(), "expected");
}""",
    """#[test]
fn test_invariant_assertion() {
    let status = 404;
    assert!(status == 200, "status must always be HTTP 200 OK");
}""",
    """pub fn infinite_recursion(n: u64) -> u64 {
    infinite_recursion(n + 1)
}"""
]

TEMPLATES_BY_CATEGORY = {
    0: CLEAN_TEMPLATES,
    1: SYNTAX_ERROR_TEMPLATES,
    2: TYPE_MISMATCH_TEMPLATES,
    3: BORROW_CHECK_FAIL_TEMPLATES,
    4: TEST_REGRESSION_TEMPLATES,
}


# --- 2. 32-Dimensional AST & Lexical Feature Extraction ---

def extract_ast_features(text: str, seq_len: int = MAX_SEQ_LEN) -> np.ndarray:
    """
    Extracts a (seq_len, 32) float32 AST and structural feature matrix:
      [0..3]   Delimiter depth: brace '{', paren '(', bracket '[', indent/4
      [4..9]   Token class: keyword, identifier, literal, operator, punctuation, whitespace
      [10..14] Scope context: in_fn, in_struct, in_impl, in_test, in_unsafe
      [15..20] Borrow/mut markers: 'mut', '&', '&mut', 'move', 'clone', 'drop'
      [21..26] Type markers: 'i32/u64/usize', 'String/&str', 'Option', 'Result', 'Vec', 'bool'
      [27..31] Defect markers: unclosed delimiter, double-borrow signature, panic/unwrap, diff +/-, invalid token
    """
    feats = np.zeros((seq_len, AST_FEATURE_DIM), dtype=np.float32)

    brace_depth = 0
    paren_depth = 0
    bracket_depth = 0
    in_fn = 0.0
    in_struct = 0.0
    in_impl = 0.0
    in_test = 1.0 if ("#[test]" in text or "test_" in text) else 0.0
    in_unsafe = 1.0 if "unsafe" in text else 0.0

    keywords = {"fn", "let", "mut", "pub", "struct", "impl", "for", "in", "match", "if", "else", "return", "use", "async", "await"}
    types = {"u8", "u16", "u32", "u64", "i32", "i64", "usize", "String", "str", "Option", "Result", "Vec", "bool"}

    chars = list(text[:seq_len])
    for i, ch in enumerate(chars):
        if ch == '{': brace_depth += 1
        elif ch == '}': brace_depth = max(0, brace_depth - 1)
        elif ch == '(': paren_depth += 1
        elif ch == ')': paren_depth = max(0, paren_depth - 1)
        elif ch == '[': bracket_depth += 1
        elif ch == ']': bracket_depth = max(0, bracket_depth - 1)

        # 0..3: Delimiter depths
        feats[i, 0] = min(brace_depth / 5.0, 1.0)
        feats[i, 1] = min(paren_depth / 5.0, 1.0)
        feats[i, 2] = min(bracket_depth / 5.0, 1.0)
        feats[i, 3] = min((i % 4) / 4.0, 1.0)

        # 4..9: Token classification
        if ch.isalpha():
            feats[i, 4] = 1.0  # ident / alpha
        elif ch.isdigit():
            feats[i, 6] = 1.0  # numeric literal
        elif ch in "+-*/%=<>!&|":
            feats[i, 7] = 1.0  # operator
        elif ch in "{}(),;:[]":
            feats[i, 8] = 1.0  # punctuation
        elif ch.isspace():
            feats[i, 9] = 1.0  # whitespace

        # 10..14: Scope
        feats[i, 10] = in_fn
        feats[i, 11] = in_struct
        feats[i, 12] = in_impl
        feats[i, 13] = in_test
        feats[i, 14] = in_unsafe

        # 15..20: Borrow / mutation context in window
        window = text[max(0, i-6):min(len(text), i+6)]
        if "mut" in window: feats[i, 15] = 1.0
        if "&" in window: feats[i, 16] = 1.0
        if "&mut" in window: feats[i, 17] = 1.0
        if "move" in window: feats[i, 18] = 1.0
        if "clone" in window: feats[i, 19] = 1.0
        if "drop" in window: feats[i, 20] = 1.0

        # 21..26: Type markers in window
        if any(t in window for t in ("i32", "u64", "usize")): feats[i, 21] = 1.0
        if any(t in window for t in ("String", "str")): feats[i, 22] = 1.0
        if "Option" in window: feats[i, 23] = 1.0
        if "Result" in window: feats[i, 24] = 1.0
        if "Vec" in window: feats[i, 25] = 1.0
        if "bool" in window: feats[i, 26] = 1.0

        # 27..31: Defect triggers
        if brace_depth != 0 and i == len(chars) - 1: feats[i, 27] = 1.0
        if "&mut *list" in text or "mut *data" in text: feats[i, 28] = 1.0
        if any(p in window for p in ("unwrap", "assert!", "panic!")): feats[i, 29] = 1.0
        if ch in "+-": feats[i, 30] = 1.0
        if ch in ";;" or ";}" in window: feats[i, 31] = 1.0

    return feats


def text_to_token_ids(text: str, seq_len: int = MAX_SEQ_LEN) -> np.ndarray:
    """
    Byte-level deterministic tokenizer mapping text bytes into vocabulary range [4..259],
    with 0=PAD, 1=BOS, 2=EOS, 3=UNK.
    """
    ids = np.zeros(seq_len, dtype=np.int64)
    ids[0] = 1  # BOS
    raw_bytes = text.encode("utf-8")
    for i, b in enumerate(raw_bytes[:seq_len - 2]):
        ids[i + 1] = (b + 4) % VOCAB_SIZE
    ids[min(len(raw_bytes) + 1, seq_len - 1)] = 2  # EOS
    return ids


def generate_dataset(num_samples: int = 10000) -> List[Dict]:
    """
    Generates a balanced dataset of code samples with AST features and labels.
    """
    dataset = []
    samples_per_cat = num_samples // len(LABELS)

    for cat_id in range(len(LABELS)):
        templates = TEMPLATES_BY_CATEGORY[cat_id]
        for _ in range(samples_per_cat):
            base = random.choice(templates)
            # Add realistic minor variations (identifiers, variable names, literals)
            var_a = random.choice(["foo", "bar", "val", "data", "item", "buf", "counter", "res"])
            var_b = random.choice(["limit", "threshold", "max_len", "count", "stride", "offset"])
            sample_text = base.replace("data", var_a).replace("count", var_b)

            token_ids = text_to_token_ids(sample_text, MAX_SEQ_LEN)
            ast_feats = extract_ast_features(sample_text, MAX_SEQ_LEN)

            will_break = 0.0 if cat_id == 0 else 1.0
            if cat_id == 0:
                risk_score = float(np.random.uniform(0.01, 0.12))
            else:
                risk_score = float(np.random.uniform(0.70, 0.98))

            dataset.append({
                "text": sample_text,
                "input_ids": token_ids,
                "ast_features": ast_feats,
                "category": cat_id,
                "will_break": will_break,
                "risk_score": risk_score
            })

    random.shuffle(dataset)
    return dataset


if __name__ == "__main__":
    ds = generate_dataset(100)
    print(f"Generated {len(ds)} test samples.")
    sample = ds[0]
    print(f"Sample Category: {LABELS[sample['category']]}, Will Break: {sample['will_break']}, Risk: {sample['risk_score']:.2f}")
    print(f"Input IDs shape: {sample['input_ids'].shape}, AST Features shape: {sample['ast_features'].shape}")
