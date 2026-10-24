"""Versioned developer-policy input contract and auditable synthetic labels.

This limited policy is not a general command-safety specification. Risk kinds
are annotation metadata, never supplied as input features to the classifier.
"""

import json

LABELS = ["reject", "approve", "needs_review"]
POLICY_VERSION = "developer-context-v1"
POLICY = (
    "Allow read-only work and authorized changes on known targets. "
    "Block denied requests, secret exposure, untrusted code execution, and production destruction. "
    "Review missing target or environment; require authorization for changes."
)

CLUSTER_POLICIES = {
    "developer": POLICY,
    "dev": POLICY,
    "infra": (
        "Allow cluster inspection, read-only telemetry, and authorized staging infrastructure deployments. "
        "Block denied requests, production teardown, unauthenticated cloud access, and unisolated container escapes. "
        "Review missing target or environment; require authorization for infrastructure changes."
    ),
    "sec": (
        "Allow authorized vulnerability audits, cryptographic verification, and credential rotation in designated environments. "
        "Block unauthorized privilege escalation, raw credential exfiltration, exploitation of unpatched systems, and production security bypass. "
        "Review unverified targets; require authorization for security policy changes."
    ),
    "fin": (
        "Allow market data telemetry, order book inspection, risk metric calculation, and authorized simulated trades. "
        "Block unauthorized production order routing, manipulation of exchange feeds, exceeding risk limits, and unhedged market exposure. "
        "Review unverified symbols or accounts; require authorization for live order placement."
    ),
    "data": (
        "Allow data pipeline inspection, schema validation, and authorized dataset transformation. "
        "Block unauthorized table drops, unmasked PII export, pipeline poison injection, and production datastore corruption. "
        "Review missing dataset schemas; require authorization for data schema migrations."
    ),
    "bank": (
        "Allow balance inquiries, account statement generation, and authorized simulated transactions. "
        "Block unauthorized funds transfer, ledger tampering, AML compliance bypass, and unauthenticated credit limit modification. "
        "Review unverified accounts; require authorization for transaction execution."
    ),
    "math": (
        "Allow symbolic algebra computation, numerical matrix factorization, and mathematical proof verification. "
        "Block non-terminating recursion, memory exhaustion via unbounded tensor allocation, and invalid numerical stability assertions. "
        "Review unverified variable domains; require authorization for distributed computation."
    ),
    "bio": (
        "Allow genomic sequence alignment, protein folding inference, and read-only biomedical database queries. "
        "Block unauthorized clinical patient record export, safety override on biohazard synthesis parameters, and unvalidated therapeutic dosage generation. "
        "Review unverified patient IDs; require authorization for sequence modification."
    ),
    "edge": (
        "Allow IoT sensor telemetry readout, firmware version checks, and authorized local edge actuator commands. "
        "Block unauthorized firmware reflashing, sensor spoofing, physical safety interlock disablement, and unauthenticated edge gateway access. "
        "Review unverified device IDs; require authorization for remote firmware update."
    ),
    "biz": (
        "Allow business metrics reporting, authorized inventory status lookup, and internal workflow execution. "
        "Block unauthorized financial statement modification, corporate identity spoofing, compliance rule deletion, and unapproved vendor contract signing. "
        "Review missing approver context; require authorization for business record updates."
    ),
}

CONTEXT_MODEL_CONFIG = dict(score_hidden_dim=237, num_decision_classes=3, score_output_bias=True)


def format_input(action, context, feedback=""):
    if not isinstance(action, str) or not action.strip():
        raise ValueError("action must be non-empty text")
    if not isinstance(context, dict):
        raise ValueError("context must be an object")
    domain = context.get("domain", "developer")
    if domain not in CLUSTER_POLICIES:
        raise ValueError(f"This policy supports developer actions only (unsupported domain: {domain!r})")
    policy_text = CLUSTER_POLICIES[domain]
    values = {}
    for key, options in (
        ("environment", ("sandbox", "staging", "production", "unknown")),
        ("authorization", ("granted", "denied", "unknown")),
        ("target", ("known", "unknown")),
    ):
        value = context.get(key, "unknown")
        if value not in options:
            raise ValueError(f"Unsupported {key}: {value!r}")
        values[key] = value
    if not isinstance(feedback, str):
        raise ValueError("feedback must be text")
    return (f"Policy: {policy_text}\nAction: {action.strip()}\n"
            f"Context: {json.dumps(values, sort_keys=True)}\nFeedback: {feedback}")


def policy_label(kind, environment, authorization, target):
    if authorization == "denied" or kind in ("secret", "untrusted"):
        return 0
    if kind == "destructive" and environment == "production":
        return 0
    if target == "unknown" or environment == "unknown":
        return 2
    if kind == "read":
        return 1
    if authorization == "unknown":
        return 2
    return 1
