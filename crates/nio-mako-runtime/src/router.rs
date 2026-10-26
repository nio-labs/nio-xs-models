//! Deterministic Canonical URL Router for Zero-Key Documentation & Web Intelligence Lookups.
//! Maps programming libraries, security CVEs, RFC standards, kernel tunables, and devops specs
//! directly to official web docs without any third-party search engine API.

pub struct CanonicalRoute {
    pub ecosystem: &'static str,
    pub target_symbol: String,
    pub canonical_url: String,
}

pub fn resolve_canonical_url(query: &str) -> Option<CanonicalRoute> {
    let q = query.trim().to_lowercase();

    // =========================================================================
    // 1. RFC STANDARDS & PROTOCOL SPECIFICATIONS
    // =========================================================================
    if q.contains("rfc 7540") || (q.contains("http/2") && q.contains("spec")) {
        return Some(CanonicalRoute {
            ecosystem: "standards",
            target_symbol: "IETF RFC 7540 (HTTP/2)".to_string(),
            canonical_url: "https://datatracker.ietf.org/doc/html/rfc7540".to_string(),
        });
    }
    if q.contains("rfc 6455") || (q.contains("websocket") && q.contains("rfc")) {
        return Some(CanonicalRoute {
            ecosystem: "standards",
            target_symbol: "IETF RFC 6455 (WebSocket Protocol)".to_string(),
            canonical_url: "https://datatracker.ietf.org/doc/html/rfc6455".to_string(),
        });
    }
    if q.contains("rfc 9110") || (q.contains("http semantics") && q.contains("spec")) {
        return Some(CanonicalRoute {
            ecosystem: "standards",
            target_symbol: "IETF RFC 9110 (HTTP Semantics)".to_string(),
            canonical_url: "https://datatracker.ietf.org/doc/html/rfc9110".to_string(),
        });
    }
    if q.contains("semver") || q.contains("semantic versioning") {
        return Some(CanonicalRoute {
            ecosystem: "standards",
            target_symbol: "Semantic Versioning 2.0.0".to_string(),
            canonical_url: "https://semver.org/spec/v2.0.0.html".to_string(),
        });
    }

    // =========================================================================
    // 2. SECURITY & CVE ADVISORIES
    // =========================================================================
    if q.contains("cve-2024-3094") || q.contains("xz backdoor") {
        return Some(CanonicalRoute {
            ecosystem: "security",
            target_symbol: "CVE-2024-3094 (XZ Utils Backdoor)".to_string(),
            canonical_url: "https://nvd.nist.gov/vuln/detail/CVE-2024-3094".to_string(),
        });
    }
    if q.contains("content-security-policy") || q.contains("csp header") {
        return Some(CanonicalRoute {
            ecosystem: "security",
            target_symbol: "Content-Security-Policy (CSP)".to_string(),
            canonical_url: "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy".to_string(),
        });
    }
    if q.contains("strict-transport-security") || q.contains("hsts header") {
        return Some(CanonicalRoute {
            ecosystem: "security",
            target_symbol: "Strict-Transport-Security (HSTS)".to_string(),
            canonical_url: "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security".to_string(),
        });
    }

    // =========================================================================
    // 3. LINUX KERNEL, SYSCTL & OS INTERNALS
    // =========================================================================
    if q.contains("tcp_tw_reuse") || (q.contains("sysctl") && q.contains("tcp")) {
        return Some(CanonicalRoute {
            ecosystem: "kernel",
            target_symbol: "net.ipv4.tcp_tw_reuse".to_string(),
            canonical_url: "https://www.kernel.org/doc/Documentation/networking/ip-sysctl.txt".to_string(),
        });
    }
    if q.contains("sqlite wal") || (q.contains("sqlite") && q.contains("write ahead log")) {
        return Some(CanonicalRoute {
            ecosystem: "database",
            target_symbol: "SQLite Write-Ahead Logging (WAL)".to_string(),
            canonical_url: "https://sqlite.org/wal.html".to_string(),
        });
    }

    // =========================================================================
    // 4. CLOUD INFRASTRUCTURE & SERVICE STATUS
    // =========================================================================
    if q.contains("github status") || (q.contains("github") && q.contains("incident")) {
        return Some(CanonicalRoute {
            ecosystem: "cloud_status",
            target_symbol: "GitHub System Status".to_string(),
            canonical_url: "https://www.githubstatus.com/".to_string(),
        });
    }
    if q.contains("cloudflare status") || (q.contains("cloudflare") && q.contains("incident")) {
        return Some(CanonicalRoute {
            ecosystem: "cloud_status",
            target_symbol: "Cloudflare Status Dashboard".to_string(),
            canonical_url: "https://www.cloudflarestatus.com/".to_string(),
        });
    }

    // =========================================================================
    // 5. PROGRAMMING RUNTIMES & ECOSYSTEMS
    // =========================================================================
    // Rust (docs.rs)
    if q.contains("tokio::sync::broadcast") || (q.contains("tokio") && q.contains("broadcast")) {
        return Some(CanonicalRoute {
            ecosystem: "rust",
            target_symbol: "tokio::sync::broadcast".to_string(),
            canonical_url: "https://docs.rs/tokio/latest/tokio/sync/broadcast/index.html".to_string(),
        });
    }
    if q.contains("axum::routing") || (q.contains("axum") && (q.contains("router") || q.contains("route"))) {
        return Some(CanonicalRoute {
            ecosystem: "rust",
            target_symbol: "axum::routing::Router".to_string(),
            canonical_url: "https://docs.rs/axum/latest/axum/routing/struct.Router.html".to_string(),
        });
    }
    if q.contains("serde::de") || (q.contains("serde") && q.contains("deserialize")) {
        return Some(CanonicalRoute {
            ecosystem: "rust",
            target_symbol: "serde::de::Deserialize".to_string(),
            canonical_url: "https://docs.rs/serde/latest/serde/de/trait.Deserialize.html".to_string(),
        });
    }
    if q.contains("reqwest::client") || (q.contains("reqwest") && q.contains("client")) {
        return Some(CanonicalRoute {
            ecosystem: "rust",
            target_symbol: "reqwest::Client".to_string(),
            canonical_url: "https://docs.rs/reqwest/latest/reqwest/struct.Client.html".to_string(),
        });
    }
    if q.contains("sqlx::query") || (q.contains("sqlx") && q.contains("query")) {
        return Some(CanonicalRoute {
            ecosystem: "rust",
            target_symbol: "sqlx::query::QueryAs".to_string(),
            canonical_url: "https://docs.rs/sqlx/latest/sqlx/struct.QueryAs.html".to_string(),
        });
    }

    // TypeScript & Web Standards (MDN)
    if q.contains("abortcontroller") || (q.contains("abort") && q.contains("signal")) {
        return Some(CanonicalRoute {
            ecosystem: "typescript",
            target_symbol: "AbortController".to_string(),
            canonical_url: "https://developer.mozilla.org/en-US/docs/Web/API/AbortController".to_string(),
        });
    }
    if q.contains("readablestream") || (q.contains("stream") && q.contains("getreader")) {
        return Some(CanonicalRoute {
            ecosystem: "typescript",
            target_symbol: "ReadableStream".to_string(),
            canonical_url: "https://developer.mozilla.org/en-US/docs/Web/API/ReadableStream".to_string(),
        });
    }
    if q.contains("subtlecrypto") || (q.contains("crypto") && q.contains("subtle")) {
        return Some(CanonicalRoute {
            ecosystem: "typescript",
            target_symbol: "SubtleCrypto".to_string(),
            canonical_url: "https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto".to_string(),
        });
    }
    if q.contains("websocket") {
        return Some(CanonicalRoute {
            ecosystem: "typescript",
            target_symbol: "WebSocket".to_string(),
            canonical_url: "https://developer.mozilla.org/en-US/docs/Web/API/WebSocket".to_string(),
        });
    }
    if q.contains("urlsearchparams") {
        return Some(CanonicalRoute {
            ecosystem: "typescript",
            target_symbol: "URLSearchParams".to_string(),
            canonical_url: "https://developer.mozilla.org/en-US/docs/Web/API/URLSearchParams".to_string(),
        });
    }

    // Python (docs.python.org / pypi)
    if q.contains("asyncio.taskgroup") || (q.contains("asyncio") && q.contains("taskgroup")) {
        return Some(CanonicalRoute {
            ecosystem: "python",
            target_symbol: "asyncio.TaskGroup".to_string(),
            canonical_url: "https://docs.python.org/3/library/asyncio-task.html#asyncio.TaskGroup".to_string(),
        });
    }
    if q.contains("httpx.asyncclient") || (q.contains("httpx") && q.contains("client")) {
        return Some(CanonicalRoute {
            ecosystem: "python",
            target_symbol: "httpx.AsyncClient".to_string(),
            canonical_url: "https://www.python-httpx.org/async/".to_string(),
        });
    }
    if q.contains("pydantic.basemodel") || (q.contains("pydantic") && (q.contains("model") || q.contains("validate"))) {
        return Some(CanonicalRoute {
            ecosystem: "python",
            target_symbol: "pydantic.BaseModel".to_string(),
            canonical_url: "https://docs.pydantic.dev/latest/api/base_model/".to_string(),
        });
    }
    if q.contains("asyncio") && q.contains("gather") {
        return Some(CanonicalRoute {
            ecosystem: "python",
            target_symbol: "asyncio.gather".to_string(),
            canonical_url: "https://docs.python.org/3/library/asyncio-task.html#asyncio.gather".to_string(),
        });
    }
    if q.contains("sqlite3") {
        return Some(CanonicalRoute {
            ecosystem: "python",
            target_symbol: "sqlite3".to_string(),
            canonical_url: "https://docs.python.org/3/library/sqlite3.html".to_string(),
        });
    }

    // Go (pkg.go.dev)
    if q.contains("errgroup") || q.contains("sync/errgroup") {
        return Some(CanonicalRoute {
            ecosystem: "go",
            target_symbol: "golang.org/x/sync/errgroup".to_string(),
            canonical_url: "https://pkg.go.dev/golang.org/x/sync/errgroup".to_string(),
        });
    }
    if q.contains("net/http.transport") || (q.contains("http") && q.contains("transport")) {
        return Some(CanonicalRoute {
            ecosystem: "go",
            target_symbol: "net/http.Transport".to_string(),
            canonical_url: "https://pkg.go.dev/net/http#Transport".to_string(),
        });
    }
    if q.contains("sync") && (q.contains("waitgroup") || q.contains("mutex")) {
        return Some(CanonicalRoute {
            ecosystem: "go",
            target_symbol: "sync.WaitGroup".to_string(),
            canonical_url: "https://pkg.go.dev/sync#WaitGroup".to_string(),
        });
    }
    if q.contains("context") && (q.contains("withtimeout") || q.contains("cancel")) {
        return Some(CanonicalRoute {
            ecosystem: "go",
            target_symbol: "context.WithTimeout".to_string(),
            canonical_url: "https://pkg.go.dev/context#WithTimeout".to_string(),
        });
    }
    if q.contains("database/sql") || (q.contains("sql") && q.contains("setmaxopenconns")) {
        return Some(CanonicalRoute {
            ecosystem: "go",
            target_symbol: "database/sql".to_string(),
            canonical_url: "https://pkg.go.dev/database/sql".to_string(),
        });
    }

    // DevOps & Infra
    if q.contains("podspec") || (q.contains("kubernetes") && q.contains("pod")) {
        return Some(CanonicalRoute {
            ecosystem: "devops",
            target_symbol: "kubernetes.v1.PodSpec".to_string(),
            canonical_url: "https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/".to_string(),
        });
    }
    if q.contains("docker compose") || q.contains("compose-file") || q.contains("depends_on") {
        return Some(CanonicalRoute {
            ecosystem: "devops",
            target_symbol: "docker.compose.v2".to_string(),
            canonical_url: "https://docs.docker.com/compose/compose-file/".to_string(),
        });
    }
    if q.contains("nginx") {
        return Some(CanonicalRoute {
            ecosystem: "devops",
            target_symbol: "nginx.proxy".to_string(),
            canonical_url: "https://nginx.org/en/docs/http/ngx_http_proxy_module.html".to_string(),
        });
    }
    if q.contains("systemd") {
        return Some(CanonicalRoute {
            ecosystem: "devops",
            target_symbol: "systemd.service".to_string(),
            canonical_url: "https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html".to_string(),
        });
    }
    if q.contains("github actions") || q.contains("workflow") {
        return Some(CanonicalRoute {
            ecosystem: "devops",
            target_symbol: "github.actions.workflow".to_string(),
            canonical_url: "https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions".to_string(),
        });
    }

    None
}
