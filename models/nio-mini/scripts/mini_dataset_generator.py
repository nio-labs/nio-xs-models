"""
NioMini High-Diversity Synthetic & Structural AST Diff Dataset Generator
Generates realistic code samples across 5 defect categories:
  0: CLEAN
  1: SYNTAX_ERROR
  2: TYPE_MISMATCH
  3: BORROW_CHECK_FAIL
  4: TEST_REGRESSION

Guarantees high diversity, sequence length of 128, and unique model inputs.
"""

import random
import re
import hashlib
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

FN_NAMES = [
    "add", "sub", "multiply", "divide", "mod_op", "calculate_hash", "process_items",
    "find_entry", "fetch_status", "sanitize_buffer", "parse_pair", "compute_total",
    "validate_range", "update_cache", "format_output", "build_index", "filter_active",
    "transform_coords", "merge_sorted", "encode_base64", "decode_utf8", "clamp_val"
]

VAR_NAMES = [
    "a", "b", "x", "y", "z", "data", "count", "item", "buf", "val", "limit",
    "stride", "offset", "res", "delta", "ptr", "idx", "len_val", "score", "tag"
]

TYPES = ["i32", "i64", "u32", "u64", "usize", "f32", "f64"]


def strip_comments(text: str) -> str:
    """Strips comments so that comment prefixes do not shadow active code defects."""
    text_no_block = re.sub(r'/\*.*?\*/', ' ', text, flags=re.DOTALL)
    lines = []
    for line in text_no_block.splitlines(True):
        trimmed = line.strip()
        if not trimmed.startswith('//'):
            if '//' in line:
                idx = line.find('//')
                lines.append(line[:idx] + '\n')
            else:
                lines.append(line)
    res = ''.join(lines).strip()
    return res if res else text


def generate_clean_sample(sample_idx: int) -> str:
    pattern = sample_idx % 8
    fn_name = random.choice(FN_NAMES) + f"_{sample_idx}"
    v1 = random.choice(VAR_NAMES)
    v2 = random.choice([v for v in VAR_NAMES if v != v1])
    t1 = random.choice(TYPES)
    t2 = t1
    val = random.randint(1, 1000)

    if pattern == 0:
        op = random.choice(["+", "-", "*"])
        return f"pub fn {fn_name}({v1}: {t1}, {v2}: {t2}) -> {t1} {{\n    {v1} {op} {v2}\n}}"
    elif pattern == 1:
        return f"pub fn {fn_name}({v1}: {t1}, min_val: {t1}, max_val: {t1}) -> bool {{\n    {v1} >= min_val && {v1} <= max_val\n}}"
    elif pattern == 2:
        return (
            f"pub fn {fn_name}({v1}: &[u8]) -> u64 {{\n"
            f"    let mut hash = {val}u64;\n"
            f"    for &byte in {v1} {{\n"
            f"        hash = hash.wrapping_mul(33).wrapping_add(byte as u64);\n"
            f"    }}\n"
            f"    hash\n"
            f"}}"
        )
    elif pattern == 3:
        struct_name = f"Worker_{sample_idx}"
        return (
            f"pub struct {struct_name} {{\n"
            f"    pub id: {t1},\n"
            f"    pub active: bool,\n"
            f"}}\n\n"
            f"impl {struct_name} {{\n"
            f"    pub fn new(id: {t1}) -> Self {{\n"
            f"        Self {{ id, active: true }}\n"
            f"    }}\n"
            f"}}"
        )
    elif pattern == 4:
        return (
            f"pub fn {fn_name}(records: &[(String, {t1})], target: &str) -> Option<{t1}> {{\n"
            f"    records.iter().find(|(k, _)| k == target).map(|(_, v)| *v)\n"
            f"}}"
        )
    elif pattern == 5:
        return (
            f"pub fn {fn_name}(mut {v1}: Vec<{t1}>, delta: {t1}) -> Vec<{t1}> {{\n"
            f"    for x in {v1}.iter_mut() {{\n"
            f"        *x += delta;\n"
            f"    }}\n"
            f"    {v1}\n"
            f"}}"
        )
    elif pattern == 6:
        return (
            f"pub fn {fn_name}(s: &str) -> Result<{t1}, std::num::ParseIntError> {{\n"
            f"    let val = s.trim().parse::<{t1}>()?;\n"
            f"    Ok(val + {val % 10})\n"
            f"}}"
        )
    else:
        return f"pub fn {fn_name}({v1}: {t1}) -> {t1} {{\n    let {v2} = {v1} + {val};\n    {v2}\n}}"


def generate_syntax_error_sample(sample_idx: int) -> str:
    pattern = sample_idx % 6
    fn_name = random.choice(FN_NAMES) + f"_{sample_idx}"
    v1 = random.choice(VAR_NAMES)
    v2 = random.choice([v for v in VAR_NAMES if v != v1])
    t1 = random.choice(TYPES)

    if pattern == 0:
        return f"pub fn {fn_name}({v1}: {t1}) -> {t1} {{\n    let {v2} = {v1} + 1;\n    {v2}"
    elif pattern == 1:
        return f"pub fn {fn_name}({v1}: {t1}] {{\n    let {v2} = {v1};\n}}"
    elif pattern == 2:
        return f"fn main() {{\n    let {v1} = ;\n    println!(\"{{}}\", {v1});\n}}"
    elif pattern == 3:
        return f"pub fn {fn_name}({v1}: {t1}) -> bool {{\n    if ({v1} > 10 && {v1} < 100 {{\n        true\n    }} else {{\n        false\n    }}\n}}"
    elif pattern == 4:
        return f"pub fn {fn_name}({v1}: {t1}) -> {t1} {{\n    let {v2} = {v1} + 10\n    {v2}\n}}"
    else:
        return f"pub fn {fn_name}() -> &'static str {{\n    let msg = \"broken string literal;\n    msg\n}}"


def generate_type_mismatch_sample(sample_idx: int) -> str:
    pattern = sample_idx % 5
    fn_name = random.choice(FN_NAMES) + f"_{sample_idx}"
    v1 = random.choice(VAR_NAMES)

    if pattern == 0:
        return f"fn main() {{\n    let {v1}: u32 = \"text_{sample_idx}\";\n    println!(\"{{}}\", {v1});\n}}"
    elif pattern == 1:
        return f"pub fn {fn_name}() -> u64 {{\n    return -1;\n}}"
    elif pattern == 2:
        return f"error[E0308]: mismatched types\n  --> src/lib.rs:{sample_idx}:5\n   |\n   | expected `String`, found `i32`"
    elif pattern == 3:
        return f"pub fn {fn_name}() -> String {{\n    let {v1} = 42;\n    {v1}\n}}"
    else:
        return f"pub fn {fn_name}({v1}: i32, s: &str) -> i32 {{\n    {v1} + s\n}}"


def generate_borrow_check_sample(sample_idx: int) -> str:
    pattern = sample_idx % 4
    v1 = random.choice(VAR_NAMES)

    if pattern == 0:
        return (
            f"fn main() {{\n"
            f"    let mut {v1} = {sample_idx};\n"
            f"    let a = &mut {v1};\n"
            f"    let b = &mut {v1};\n"
            f"    println!(\"{{}} {{}}\", a, b);\n"
            f"}}"
        )
    elif pattern == 1:
        return f"error[E0499]: cannot borrow `*{v1}` as mutable more than once at a time\n  --> src/main.rs:{sample_idx}:13"
    elif pattern == 2:
        return (
            f"pub fn process_data_{sample_idx}() {{\n"
            f"    let s = String::from(\"data_{sample_idx}\");\n"
            f"    let consumer = s;\n"
            f"    println!(\"{{}}\", s);\n"
            f"}}"
        )
    else:
        return f"pub fn get_local_ref_{sample_idx}() -> &i32 {{\n    let local = 42;\n    &local\n}}"


def generate_test_regression_sample(sample_idx: int) -> str:
    pattern = sample_idx % 4
    test_name = f"test_{sample_idx}"

    if pattern == 0:
        return f"#[test]\nfn {test_name}() {{\n    assert!(false);\n}}"
    elif pattern == 1:
        return f"#[test]\nfn {test_name}() {{\n    let result = true;\n    let expected = true;\n    assert_eq!(result, !expected);\n}}"
    elif pattern == 2:
        return f"test result: FAILED. {sample_idx} passed; 1 failed; 0 ignored; finished in 0.05s"
    else:
        return f"#[test]\nfn {test_name}() {{\n    panic!(\"regression defect in commit {sample_idx}\");\n}}"


# --- 2. Deterministic Tokenization (128 Positions) ---

def text_to_token_ids(text: str, seq_len: int = MAX_SEQ_LEN) -> np.ndarray:
    """
    Converts text diff/code into deterministic byte token IDs:
      0: PAD
      1: BOS
      2: EOS
      3: UNK
      4..259: Raw Byte values (b + 4)
    Strips comment padding so active code defects are not discarded.
    """
    effective_text = strip_comments(text)
    ids = np.zeros(seq_len, dtype=np.int64)
    ids[0] = 1  # BOS

    raw_bytes = effective_text.encode("utf-8")
    if len(raw_bytes) > seq_len - 2:
        raw_bytes = raw_bytes[: seq_len - 2]

    for i, b in enumerate(raw_bytes):
        ids[i + 1] = (b + 4) % VOCAB_SIZE

    ids[min(len(raw_bytes) + 1, seq_len - 1)] = 2  # EOS
    return ids


# --- 3. 32-Dimensional AST Feature Extraction ---

def extract_ast_features(text: str, seq_len: int = MAX_SEQ_LEN) -> np.ndarray:
    """
    Extracts a 32-dimensional structural AST feature tensor across seq_len positions.
    """
    effective_text = strip_comments(text)
    feats = np.zeros((seq_len, AST_FEATURE_DIM), dtype=np.float32)

    brace_depth = 0
    paren_depth = 0
    bracket_depth = 0

    has_assert_false = "assert!(false)" in effective_text or "assert_eq!(result, !expected)" in effective_text
    has_empty_assign = "= ;" in effective_text or "=;" in effective_text
    has_double_borrow = bool(re.search(r"&mut\s+(\w+).*&mut\s+\1", effective_text, re.DOTALL))
    has_compiler_err = "error[" in effective_text or "mismatched types" in effective_text or "test result: FAILED" in effective_text

    chars = list(effective_text[:seq_len])
    for i, ch in enumerate(chars):
        if ch == '{': brace_depth += 1
        elif ch == '}': brace_depth = max(0, brace_depth - 1)
        elif ch == '(': paren_depth += 1
        elif ch == ')': paren_depth = max(0, paren_depth - 1)
        elif ch == '[': bracket_depth += 1
        elif ch == ']': bracket_depth = max(0, bracket_depth - 1)

        feats[i, 0] = min(brace_depth / 5.0, 1.0)
        feats[i, 1] = min(paren_depth / 5.0, 1.0)
        feats[i, 2] = min(bracket_depth / 5.0, 1.0)
        feats[i, 3] = min((i % 4) / 4.0, 1.0)

        if ch.isalpha():
            feats[i, 4] = 1.0
        elif ch.isdigit():
            feats[i, 6] = 1.0
        elif ch in "+-*/%=<>!&|":
            feats[i, 7] = 1.0
        elif ch in "{}(),;:[]":
            feats[i, 8] = 1.0
        elif ch.isspace():
            feats[i, 9] = 1.0

        feats[i, 10] = 1.0 if "fn " in effective_text else 0.0
        feats[i, 11] = 1.0 if "struct " in effective_text else 0.0
        feats[i, 12] = 1.0 if "impl " in effective_text else 0.0
        feats[i, 13] = 1.0 if "#[test]" in effective_text else 0.0
        feats[i, 14] = 1.0 if "panic!" in effective_text else 0.0

        window = effective_text[max(0, i-6):min(len(effective_text), i+6)]
        if "mut" in window: feats[i, 15] = 1.0
        if "&" in window: feats[i, 16] = 1.0
        if "&mut" in window: feats[i, 17] = 1.0
        if "move" in window: feats[i, 18] = 1.0
        if "clone" in window: feats[i, 19] = 1.0
        if "drop" in window: feats[i, 20] = 1.0

        if any(t in window for t in ("i32", "u64", "usize")): feats[i, 21] = 1.0
        if any(t in window for t in ("String", "str")): feats[i, 22] = 1.0
        if "Option" in window: feats[i, 23] = 1.0
        if "Result" in window: feats[i, 24] = 1.0
        if "Vec" in window: feats[i, 25] = 1.0
        if "bool" in window: feats[i, 26] = 1.0

        if has_empty_assign: feats[i, 27] = 1.0
        if has_double_borrow: feats[i, 28] = 1.0
        if has_assert_false: feats[i, 29] = 1.0
        if has_compiler_err: feats[i, 30] = 1.0
        if brace_depth != 0 and i == len(chars) - 1: feats[i, 31] = 1.0

    return feats


# --- 4. High-Diversity Dataset Generator with 100% Uniqueness Guarantee ---

def generate_dataset(num_samples: int = 10000) -> List[Dict]:
    dataset = []
    samples_per_cat = num_samples // len(LABELS)
    seen_signatures = set()

    generators = [
        generate_clean_sample,
        generate_syntax_error_sample,
        generate_type_mismatch_sample,
        generate_borrow_check_sample,
        generate_test_regression_sample,
    ]

    for cat_id, gen_fn in enumerate(generators):
        target_count = samples_per_cat if cat_id < len(LABELS) - 1 else (num_samples - len(dataset))
        count = 0
        idx = 0

        if cat_id == 0:
            base_add = "pub fn add(a: i32, b: i32) -> i32 { a + b }"
            t_ids = text_to_token_ids(base_add, MAX_SEQ_LEN)
            a_feats = extract_ast_features(base_add, MAX_SEQ_LEN)
            sig = hashlib.sha256(t_ids.tobytes() + a_feats.tobytes()).digest()
            seen_signatures.add(sig)
            dataset.append({
                "text": base_add,
                "input_ids": t_ids,
                "ast_features": a_feats,
                "category": 0,
                "will_break": 0.0,
                "risk_score": 0.05,
            })
            count += 1

        while count < target_count:
            idx += 1
            sample_text = gen_fn(idx)
            token_ids = text_to_token_ids(sample_text, MAX_SEQ_LEN)
            ast_feats = extract_ast_features(sample_text, MAX_SEQ_LEN)

            sig = hashlib.sha256(token_ids.tobytes() + ast_feats.tobytes()).digest()
            if sig in seen_signatures:
                continue

            seen_signatures.add(sig)

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
                "risk_score": risk_score,
            })
            count += 1

    random.shuffle(dataset)
    return dataset


if __name__ == "__main__":
    ds = generate_dataset(100)
    print(f"Generated {len(ds)} test samples.")
    sample = ds[0]
    print(f"Sample Category: {LABELS[sample['category']]}, Will Break: {sample['will_break']}, Risk: {sample['risk_score']:.2f}")
    print(f"Input IDs shape: {sample['input_ids'].shape}, AST Features shape: {sample['ast_features'].shape}")
