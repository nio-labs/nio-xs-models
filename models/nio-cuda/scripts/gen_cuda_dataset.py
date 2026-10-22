#!/usr/bin/env python3
"""
gen_cuda_dataset.py — Synthetic High-Signal Swarm Conductor Dataset Generator for NioCuda (~310M)
Generates structured execution plans (<cuda_plan> and <cuda_dag>) orchestrating the Nio predator fleet:
  - nio-nano: AST symbol navigation, file indexing, symbol triage
  - nio-ray: Keystroke code generation, inline code completion
  - nio-viper: Terminal execution, bash commands, build & test verification
  - nio-mini: AST linting, syntax & defect auditing
  - nio-micro: Governance & security policy verdict, diff approval
  - nio-manta: High-level architectural dialogue and user communication
"""

import json
import random
from pathlib import Path

OUTPUT_FILE = Path(__file__).resolve().parent / "nio_cuda_conductor_data.jsonl"

TEMPLATES = [
    {
        "domain": "security_refactor",
        "tasks": [
            ("Upgrade password hashing from bcrypt to Argon2id in authentication service",
             "auth-argon2-upgrade",
             "crates/auth/src/hash.rs",
             "cargo test -p auth --test test_password_hash"),
            ("Sanitize SQL input parameters in user search query handler",
             "sql-sanitize-user-query",
             "src/db/queries/users.rs",
             "cargo test --test db_security_tests"),
            ("Replace insecure MD5 checksums with SHA-256 in artifact validator",
             "artifact-sha256-fix",
             "crates/core/src/checksum.rs",
             "cargo test --test checksum_verification"),
            ("Implement JWT revocation blacklist in Redis cache layer",
             "jwt-revocation-redis",
             "crates/auth/src/token_blacklist.rs",
             "cargo test -p auth --test token_revocation"),
            ("Patch path traversal vulnerability in static asset server",
             "path-traversal-patch",
             "crates/server/src/static_files.rs",
             "cargo test -p server --test path_safety_suite"),
            ("Enforce TLS 1.3 minimum cipher suites in rustls configuration",
             "rustls-tls13-enforce",
             "crates/network/src/tls.rs",
             "cargo test -p network --test tls_handshake_tests"),
            ("Harden CORS headers to forbid wildcard origins with credentials",
             "cors-security-harden",
             "crates/gateway/src/middleware/cors.rs",
             "cargo test -p gateway --test cors_policies"),
            ("Prevent timing attack in HMAC signature comparison using subtle::ConstantTimeEq",
             "hmac-constant-time-compare",
             "crates/crypto/src/hmac.rs",
             "cargo test -p crypto --test constant_time_tests"),
        ]
    },
    {
        "domain": "feature_addition",
        "tasks": [
            ("Add health check endpoint with uptime and memory metrics to Axum router",
             "axum-health-check-metrics",
             "crates/server/src/routes/health.rs",
             "curl -fsSL http://127.0.0.1:8080/health && cargo test --test health_check"),
            ("Implement rate limiting middleware using token bucket algorithm",
             "rate-limiting-middleware",
             "crates/gateway/src/middleware/rate_limit.rs",
             "cargo test -p gateway --test rate_limiter_load"),
            ("Add Prometheus metrics exporter for HTTP request latency",
             "prometheus-metrics-exporter",
             "crates/telemetry/src/prometheus.rs",
             "cargo test -p telemetry --test metric_export"),
            ("Add JSON Lines log formatter with tracing-subscriber",
             "tracing-jsonl-logger",
             "crates/core/src/logging.rs",
             "cargo test -p core --test logging_format"),
            ("Implement graceful shutdown handler for SIGTERM and SIGINT",
             "graceful-shutdown-handler",
             "src/main.rs",
             "cargo test --test shutdown_integration"),
            ("Add CLI command `nioxs inspect` using clap v4 parser",
             "clap-inspect-command",
             "crates/cli/src/commands/inspect.rs",
             "cargo run -- inspect --help"),
            ("Implement exponential backoff retry policy for external webhook dispatcher",
             "webhook-retry-backoff",
             "crates/webhooks/src/dispatcher.rs",
             "cargo test -p webhooks --test retry_logic"),
            ("Add OpenTelemetry distributed tracing context propagation to gRPC calls",
             "otel-grpc-tracing",
             "crates/rpc/src/interceptors/trace.rs",
             "cargo test -p rpc --test trace_context_propagation"),
        ]
    },
    {
        "domain": "bug_fix",
        "tasks": [
            ("Resolve dead lock in thread pool during async task cancellation",
             "fix-threadpool-deadlock",
             "crates/runtime/src/pool.rs",
             "cargo test -p runtime --test dead_lock_stress"),
            ("Fix memory leak caused by unclosed Tokio broadcast subscriber channels",
             "fix-broadcast-memory-leak",
             "crates/events/src/bus.rs",
             "cargo test -p events --test subscriber_leak_audit"),
            ("Prevent integer overflow during byte offset computation in chunked reader",
             "fix-chunk-offset-overflow",
             "crates/io/src/chunk_reader.rs",
             "cargo test -p io --test chunk_boundary_tests"),
            ("Handle broken pipe EPIPE gracefully in stdout streaming logger",
             "fix-broken-pipe-handling",
             "crates/logger/src/writer.rs",
             "cargo test -p logger --test broken_pipe_resilience"),
            ("Fix unhandled error in JSON deserialization of nullable array fields",
             "fix-json-nullable-array",
             "crates/schema/src/parser.rs",
             "cargo test -p schema --test nullable_deserialization"),
            ("Fix off-by-one error in sliding window token counter",
             "fix-token-sliding-window",
             "crates/tokens/src/window.rs",
             "cargo test -p tokens --test sliding_window_bounds"),
            ("Prevent panic on empty buffer when parsing HTTP chunked transfer headers",
             "fix-empty-buffer-chunked-header",
             "crates/http/src/chunked.rs",
             "cargo test -p http --test chunk_header_empty"),
            ("Fix race condition between cache invalidation and database write commit",
             "fix-cache-invalidation-race",
             "crates/cache/src/sync.rs",
             "cargo test -p cache --test cache_sync_race"),
        ]
    },
    {
        "domain": "performance_optimization",
        "tasks": [
            ("Optimize JSON serialization with simd-json and zero-copy borrows",
             "opt-simd-json-zerocopy",
             "crates/codec/src/json.rs",
             "cargo bench --bench json_throughput"),
            ("Replace Mutex with atomic integers for monotonic request counter",
             "opt-atomic-request-counter",
             "crates/metrics/src/counter.rs",
             "cargo bench --bench counter_concurrency"),
            ("Cache compiled regex patterns in once_cell / LazyLock static singleton",
             "opt-regex-lazylock",
             "crates/router/src/matcher.rs",
             "cargo test -p router && cargo bench --bench route_matching"),
            ("Preallocate capacity for vector buffers in hot event ingestion loop",
             "opt-preallocate-vec-buffers",
             "crates/ingest/src/buffer.rs",
             "cargo bench --bench ingest_throughput"),
            ("Optimize GGUF tensor memory layout for 32-byte SIMD alignment",
             "opt-gguf-simd-32byte-align",
             "crates/quant/src/align.rs",
             "cargo test -p quant --test alignment_verification"),
            ("Reduce memory allocations in string tokenizer using Cow<'static, str>",
             "opt-cow-string-alloc",
             "crates/tokenizer/src/fast_tok.rs",
             "cargo bench --bench tokenizer_bench"),
        ]
    },
    {
        "domain": "refactoring_migration",
        "tasks": [
            ("Migrate Actix-web route definitions to Axum router style handlers",
             "migrate-actix-to-axum",
             "src/routes/api.rs",
             "cargo check && cargo test --test api_contract"),
            ("Deprecate legacy sync std::fs calls with tokio::fs async file operations",
             "migrate-sync-fs-to-tokio",
             "crates/storage/src/file_store.rs",
             "cargo test -p storage --test async_io"),
            ("Refactor monolith error enum into domain-specific thiserror types",
             "refactor-domain-errors",
             "crates/core/src/errors.rs",
             "cargo check --workspace --all-targets"),
            ("Extract configuration parsing into standalone validation layer",
             "refactor-config-validation",
             "crates/config/src/validator.rs",
             "cargo test -p config --test validation_suite"),
            ("Convert raw SQL strings to type-safe SQLx query_as macros",
             "migrate-sqlx-macros",
             "crates/db/src/queries.rs",
             "cargo test -p db --test query_typecheck"),
        ]
    }
]

SYSTEM_PROMPT = (
    "You are NioCuda, the tactical swarm conductor and air-traffic controller for NioXS. "
    "You synthesize developer tasks into atomic, deterministic coordination plans across the Nio fleet: "
    "nio-nano (AST navigation & triage), nio-ray (keystroke code generation), "
    "nio-mini (defect & lint audit), nio-viper (terminal & test execution), "
    "and nio-micro (policy verdict & approval). "
    "Always output valid <cuda_plan> or <cuda_dag> XML specifications."
)

def make_sample(task, plan_id, target_file, test_cmd, mode="plan"):
    user_prompt = f"Coordinate the swarm to execute this task: {task}"
    
    if mode == "plan":
        response = (
            f"Tactical plan initialized for task '{task}'.\n\n"
            f"<cuda_plan task=\"{task}\" goal=\"Deterministic zero-defect completion\">\n"
            f"  <stage id=\"1\" model=\"nio-nano\" action=\"symbol_triage\" path=\"{target_file}\" goal=\"Index AST symbols and map references\" />\n"
            f"  <stage id=\"2\" model=\"nio-ray\" action=\"keystroke_code\" file=\"{target_file}\" task=\"{task}\" />\n"
            f"  <stage id=\"3\" model=\"nio-mini\" action=\"defect_audit\" file=\"{target_file}\" target=\"AST syntax and safety rules\" />\n"
            f"  <stage id=\"4\" model=\"nio-viper\" action=\"terminal_verify\" cmd=\"{test_cmd}\" />\n"
            f"  <stage id=\"5\" model=\"nio-micro\" action=\"policy_verdict\" scope=\"Diff approval & final merge check\" />\n"
            f"</cuda_plan>"
        )
    else:
        response = (
            f"Conductor DAG scheduled for '{task}'.\n\n"
            f"<cuda_dag id=\"{plan_id}\" task=\"{task}\">\n"
            f"  <node id=\"triage\" model=\"nio-nano\" action=\"symbol_triage\" path=\"{target_file}\" />\n"
            f"  <node id=\"codegen\" model=\"nio-ray\" depends_on=\"triage\" file=\"{target_file}\" task=\"{task}\" />\n"
            f"  <node id=\"audit\" model=\"nio-mini\" depends_on=\"codegen\" file=\"{target_file}\" />\n"
            f"  <node id=\"verify\" model=\"nio-viper\" depends_on=\"audit\" cmd=\"{test_cmd}\" />\n"
            f"  <node id=\"verdict\" model=\"nio-micro\" depends_on=\"verify\" policy=\"security_audit_pass\" />\n"
            f"</cuda_dag>"
        )

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": response}
        ]
    }

def main():
    samples = []
    
    # 1. Base templated pairs
    for group in TEMPLATES:
        for task, plan_id, target_file, test_cmd in group["tasks"]:
            samples.append(make_sample(task, plan_id, target_file, test_cmd, mode="plan"))
            samples.append(make_sample(task, plan_id, target_file, test_cmd, mode="dag"))

    # 2. Permutations and synthesized variations to reach 1,600+ high-signal examples
    modules = ["crates/core", "crates/crypto", "crates/db", "crates/server", "crates/auth",
               "crates/runtime", "crates/telemetry", "crates/storage", "crates/cli", "crates/gateway"]
    actions = [
        "Implement memory-safe zero-copy deserialization in",
        "Add comprehensive unit test coverage for error conditions in",
        "Refactor concurrent state synchronization using Tokio RwLock in",
        "Harden input validation and error bounds checking in",
        "Eliminate unwrap() calls and replace with proper Result bubbling in",
        "Optimize hot loop performance and eliminate allocations in",
        "Add telemetry metrics instrumentation to",
        "Verify thread safety and Send/Sync compliance in",
        "Standardize logging output with structured fields in",
        "Enforce strict lifetime bounds and borrow isolation in"
    ]
    subpaths = ["src/lib.rs", "src/state.rs", "src/handler.rs", "src/cache.rs", "src/queue.rs",
                "src/engine.rs", "src/worker.rs", "src/client.rs", "src/parser.rs", "src/validator.rs"]

    random.seed(42)
    count = 0
    while len(samples) < 1650:
        mod = random.choice(modules)
        act = random.choice(actions)
        sub = random.choice(subpaths)
        file_path = f"{mod}/{sub}"
        crate_name = mod.split("/")[1]
        task_desc = f"{act} {file_path}"
        plan_id = f"task-{crate_name}-{count}"
        test_cmd = f"cargo test -p {crate_name}"
        mode = "plan" if count % 2 == 0 else "dag"
        samples.append(make_sample(task_desc, plan_id, file_path, test_cmd, mode=mode))
        count += 1

    random.shuffle(samples)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in samples:
            f.write(json.dumps(item) + "\n")

    print(f"✅ Generated {len(samples)} NioCuda conductor samples in {OUTPUT_FILE}")
    print(f"   File size: {OUTPUT_FILE.stat().st_size / 1024:.2f} KB")

if __name__ == "__main__":
    main()
