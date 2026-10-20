"""
Synthetic Dataset Generator for NioMask (~1.0M Secret & PII Redactor)
Generates high-fidelity training data with realistic secrets, PII, and benign high-entropy counter-examples.
"""

import os
import json
import random
import string
import argparse
from typing import List, Tuple, Dict, Any

from model import VOCAB_SIZE, PAD_ID, BOS_ID, EOS_ID, LABEL_NAMES

# Helper to generate random alphanumeric strings
def rand_alnum(length: int) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))

def rand_hex(length: int) -> str:
    return "".join(random.choices("0123456789abcdef", k=length))

def rand_digits(length: int) -> str:
    return "".join(random.choices(string.digits, k=length))

def rand_base64(length: int) -> str:
    chars = string.ascii_letters + string.digits + "+/="
    return "".join(random.choices(chars, k=length))

# --- Secret Generators ---
def gen_aws_key() -> str:
    return "AKIA" + "".join(random.choices(string.ascii_uppercase + string.digits, k=16))

def gen_aws_secret() -> str:
    return rand_base64(40)

def gen_github_pat() -> str:
    return "ghp_" + rand_alnum(36)

def gen_github_fine_grained() -> str:
    return "github_pat_" + rand_alnum(82)

def gen_openai_key() -> str:
    return "sk-" + rand_alnum(48)

def gen_openai_proj_key() -> str:
    return "sk-proj-" + rand_alnum(48)

def gen_slack_token() -> str:
    return f"xoxb-{rand_digits(12)}-{rand_digits(12)}-{rand_alnum(24)}"

def gen_stripe_key() -> str:
    return "sk_live_" + rand_alnum(24)

def gen_jwt_token() -> str:
    header = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    payload = "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkFkbWluIiwiaWF0IjoxNTE2MjM5MDIyfQ"
    signature = rand_alnum(43)
    return f"{header}.{payload}.{signature}"

def gen_private_key_header() -> str:
    return "-----BEGIN RSA PRIVATE KEY-----\n" + rand_base64(32) + "\n-----END RSA PRIVATE KEY-----"

def gen_password() -> str:
    parts = [
        random.choice(["Admin", "Super", "P@ss", "Secret", "Master", "Root", "DevOps"]),
        random.choice(["99!", "2024#", "Secure$", "Key!123", "_Pass@"]),
        rand_alnum(4)
    ]
    return "".join(parts)

# --- PII Generators ---
def gen_email() -> str:
    names = ["monynith", "alex.dev", "j.smith", "sre-oncall", "cloud-admin", "user_test", "david.k"]
    domains = ["gmail.com", "nio-labs.com", "internal.io", "outlook.com", "corp.net", "protonmail.com"]
    return f"{random.choice(names)}@{random.choice(domains)}"

def gen_ipv4() -> str:
    return f"{random.randint(10, 220)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

def gen_ipv6() -> str:
    forms = [
        "::1",
        "fe80::",
        "2001:db8::",
        "2001:db8::1",
        "2001:db8::abcd:1234",
        "::ffff:192.0.2.128",
        ":".join([rand_hex(4) for _ in range(8)])
    ]
    return random.choice(forms)

def gen_phone() -> str:
    return f"+{random.randint(1, 999)}-{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"

# --- Benign High-Entropy Generators (Counter-examples to prevent False Positives) ---
def gen_git_sha() -> str:
    return rand_hex(40)

def gen_uuid() -> str:
    return f"{rand_hex(8)}-{rand_hex(4)}-4{rand_hex(3)}-8{rand_hex(3)}-{rand_hex(12)}"

def gen_docker_digest() -> str:
    return "sha256:" + rand_hex(64)


# --- Context Templates ---
SECRET_TEMPLATES = [
    ("export AWS_ACCESS_KEY_ID={val}", "AWS_ACCESS_KEY_ID="),
    ("export AWS_SECRET_ACCESS_KEY={val}", "AWS_SECRET_ACCESS_KEY="),
    ("curl -H 'Authorization: Bearer {val}' https://api.internal.com/v1", "Authorization: Bearer "),
    ("const client = new OpenAI({{ apiKey: '{val}' }});", "apiKey: '"),
    ("gh auth login --with-token <<< '{val}'", "<<< '"),
    ("STRIPE_SECRET_KEY='{val}'", "STRIPE_SECRET_KEY='"),
    ("SLACK_BOT_TOKEN=\"{val}\"", "SLACK_BOT_TOKEN=\""),
    ("git clone https://x-token-auth:{val}@github.com/repo.git", "https://x-token-auth:"),
    ("DATABASE_URL=\"postgres://postgres:{val}@db.prod:5432/app\"", "postgres:"),
    ("postgres://admin:{val}@db.prod:5432/app", "admin:"),
    ("password={val}", "password="),
    ("const privateKey = `{val}`;", "privateKey = `"),
]

PII_TEMPLATES = [
    ("User signup detected: email={val} from remote host", "email="),
    ("Notification dispatched to recipient: {val}", "recipient: "),
    ("Connecting to cluster endpoint at https://{val}:8443", "https://"),
    ("SSH session opened from {val} port 22", "from "),
    ("Customer billing phone verified: {val}", "verified: "),
    ("Support contact requested by customer {val}", "customer "),
    ("contact {val} for help", "contact "),
    ("host={val}", "host="),
]

BENIGN_HASH_TEMPLATES = [
    ("commit {val}\nAuthor: monynith <developer>", "commit "),
    ("Merge branch 'feature' into main (id: {val})", "id: "),
    ("Container image digest resolved: {val}", "resolved: "),
    ("Request trace-id generated: {val} [200 OK]", "trace-id generated: "),
    ("Asset cache key: static/bundle.{val}.js", "bundle."),
    ("Computed SHA256 checksum: {val}", "checksum: "),
]

CLEAN_TEMPLATES = [
    "cargo build --release --workspace",
    "git status -s\nM README.md\n?? src/model.rs",
    "fn process_stream(buffer: &[u8]) -> Result<Vec<u8>, StreamError> { Ok(buffer.to_vec()) }",
    "System load: 0.12, 0.24, 0.18. All health checks passing.",
    "export RUST_LOG=info\nexport NIO_RUNTIME=candle",
    "Running 14 tests in crate nio_micro_runtime... ok",
    "HTTP/1.1 200 OK\nContent-Type: application/json\n\n{\"status\":\"healthy\",\"uptime\":3600}",
    "impl Default for NioMaskConfig { fn default() -> Self { Self::new() } }",
    "Downloading weights from registry: nio_mask_v0.1.0.onnx (2.1 MB)... done.",
    "Updating crates.io index\nFetch complete in 0.42s",
    "-----BEGIN CERTIFICATE-----\nMIIDXTCCAkWgAwIBAgIJAL9\n-----END CERTIFICATE-----",
    "version 1.2.3.4",
    "mask-image border-mask-property; task-runner risk-score",
    "hello g",
    "Hello สวัสดี 世界 🌏",
]


def text_to_bytes(text: str) -> List[int]:
    """Converts a UTF-8 string to a list of byte IDs shifted by 4."""
    raw_bytes = text.encode("utf-8")
    return [b + 4 for b in raw_bytes]


def generate_sample(sample_type: str = None) -> Dict[str, Any]:
    if sample_type is None:
        sample_type = random.choices(
            ["secret", "pii", "benign_hash", "clean"],
            weights=[0.40, 0.25, 0.20, 0.15],
            k=1
        )[0]

    if sample_type == "secret":
        generator = random.choice([
            gen_aws_key, gen_aws_secret, gen_github_pat, gen_github_fine_grained,
            gen_openai_key, gen_openai_proj_key, gen_slack_token, gen_stripe_key,
            gen_jwt_token, gen_private_key_header, gen_password
        ])
        val = generator()
        template, prefix = random.choice(SECRET_TEMPLATES)
        text = template.format(val=val)
        b_label, i_label = 1, 2  # B-SECRET, I-SECRET
        risk = 1.0
        val_start = text.find(val)
        val_end = val_start + len(val)

    elif sample_type == "pii":
        generator = random.choice([gen_email, gen_ipv4, gen_ipv6, gen_phone])
        val = generator()
        template, prefix = random.choice(PII_TEMPLATES)
        text = template.format(val=val)
        b_label, i_label = 3, 4  # B-PII, I-PII
        risk = 0.7
        val_start = text.find(val)
        val_end = val_start + len(val)

    elif sample_type == "benign_hash":
        generator = random.choice([gen_git_sha, gen_uuid, gen_docker_digest])
        val = generator()
        template, prefix = random.choice(BENIGN_HASH_TEMPLATES)
        text = template.format(val=val)
        b_label, i_label = 5, 6  # B-HASH, I-HASH
        risk = 0.05
        val_start = text.find(val)
        val_end = val_start + len(val)

    else:  # clean
        text = random.choice(CLEAN_TEMPLATES)
        val_start = -1
        val_end = -1
        b_label, i_label = 0, 0
        risk = 0.0

    raw_bytes = text.encode("utf-8")
    byte_ids = [b + 4 for b in raw_bytes]
    labels = [0] * len(byte_ids)  # default 'O'

    if val_start != -1:
        # Compute byte offsets
        prefix_bytes_len = len(text[:val_start].encode("utf-8"))
        val_bytes_len = len(text[val_start:val_end].encode("utf-8"))

        if val_bytes_len > 0:
            labels[prefix_bytes_len] = b_label
            for i in range(1, val_bytes_len):
                if prefix_bytes_len + i < len(labels):
                    labels[prefix_bytes_len + i] = i_label

    return {
        "text": text,
        "input_ids": byte_ids,
        "labels": labels,
        "risk_score": risk,
    }


def generate_dataset(num_samples: int, output_file: str):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for _ in range(num_samples):
            sample = generate_sample()
            f.write(json.dumps(sample) + "\n")
    print(f"Generated {num_samples:,} samples -> {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=10000, help="Number of training samples")
    parser.add_argument("--val-samples", type=int, default=1000, help="Number of validation samples")
    parser.add_argument("--out-dir", type=str, default="data", help="Output directory")
    args = parser.parse_args()

    train_path = os.path.join(args.out_dir, "train.jsonl")
    val_path = os.path.join(args.out_dir, "val.jsonl")

    generate_dataset(args.samples, train_path)
    generate_dataset(args.val_samples, val_path)
