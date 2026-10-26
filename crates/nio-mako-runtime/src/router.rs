//! Deterministic Canonical URL Router for Zero-Key Documentation Lookups.
//! Maps standard developer library queries directly to official web docs without any search engine API.

pub struct CanonicalRoute {
    pub ecosystem: &'static str,
    pub target_symbol: String,
    pub canonical_url: String,
}

pub fn resolve_canonical_url(query: &str) -> Option<CanonicalRoute> {
    let q = query.trim().to_lowercase();

    // 1. Rust Ecosystem (docs.rs)
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

    // 2. TypeScript & Web Standards (MDN)
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

    // 3. Python Ecosystem (docs.python.org / pypi)
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

    // 4. Go Ecosystem (pkg.go.dev)
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

    // 5. DevOps & Cloud
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_canonical_routes() {
        let r1 = resolve_canonical_url("how to fix tokio broadcast channel lagged error in rust").unwrap();
        assert_eq!(r1.ecosystem, "rust");
        assert!(r1.canonical_url.contains("tokio/sync/broadcast"));

        let r2 = resolve_canonical_url("AbortController timeout in typescript").unwrap();
        assert_eq!(r2.ecosystem, "typescript");
        assert!(r2.canonical_url.contains("AbortController"));

        let r3 = resolve_canonical_url("asyncio taskgroup error handling python 3.11").unwrap();
        assert_eq!(r3.ecosystem, "python");
        assert!(r3.canonical_url.contains("asyncio-task.html"));
    }
}
