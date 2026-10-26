//! Official native Rust web intelligence & documentation scout runtime for Mako (150M) v-µLM.
//! Part of the Nio MicroLM fleet. Zero API keys, sub-millisecond pre-scrubbing, and LLM-Native Wire DSL.

pub mod router;
pub mod scrubber;
pub mod cache;
pub mod wire_dsl;
pub mod crawler;

use anyhow::{anyhow, Result};
use std::time::Instant;
use serde::{Deserialize, Serialize};

pub use router::resolve_canonical_url;
pub use scrubber::scrub_html_content;
pub use cache::MakoCache;
pub use wire_dsl::MakoWireDoc;
pub use crawler::{MakoCrawler, FetchResult};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct MakoScoutReport {
    pub query: String,
    pub target_url: String,
    pub ecosystem: String,
    pub raw_bytes: usize,
    pub scrubbed_bytes: usize,
    pub reduction_pct: f64,
    pub from_cache: bool,
    pub elapsed_ms: f64,
    pub wire_dsl: String,
}

pub fn scout_web_documentation(query: &str, force_refresh: bool) -> Result<MakoScoutReport> {
    let start = Instant::now();
    let crawler = MakoCrawler::new()?;

    // 1. Resolve target URL (Deterministic routing first, keyless search fallback)
    let (target_url, ecosystem, symbol) = if let Some(route) = resolve_canonical_url(query) {
        (route.canonical_url, route.ecosystem.to_string(), route.target_symbol)
    } else {
        let links = crawler.search_duckduckgo_lite(query)?;
        if let Some(first_link) = links.into_iter().next() {
            (first_link, "generic_web".to_string(), query.to_string())
        } else {
            return Err(anyhow!("No relevant documentation URLs found for query: {}", query));
        }
    };

    // 2. Fetch and pre-scrub HTML
    let fetch_res = crawler.fetch_and_scrub(&target_url, force_refresh)?;
    let reduction = if fetch_res.raw_bytes > 0 {
        ((fetch_res.raw_bytes as f64 - fetch_res.scrubbed_bytes as f64) / fetch_res.raw_bytes as f64) * 100.0
    } else {
        0.0
    };

    // 3. Synthesize the LLM-Native Wire DSL representation
    let mut doc = MakoWireDoc::new(&symbol, &ecosystem, &target_url);

    // Extract key semantic lines according to ecosystem domain
    for line in fetch_res.scrubbed_content.lines() {
        let l = line.trim();
        if l.is_empty() || l.starts_with('<') || l.starts_with('{') || l.starts_with('}') || l.len() < 10 {
            continue;
        }

        // 1. Signatures, Directives, Headers, and Core Specifications
        let is_spec_line = match ecosystem.as_str() {
            "standards" => {
                l.starts_with("RFC ") || l.contains("MUST ") || l.contains("SHOULD ") || l.contains("Frame") || l.contains("Opcode")
            }
            "security" => {
                l.contains("Vulnerability") || l.contains("Severity") || l.contains("CVSS") || l.contains("Backdoor") || l.contains("directive") || l.contains("nonce")
            }
            "kernel" | "database" => {
                l.contains("default") || l.contains("BOOLEAN") || l.contains("checkpoint") || l.contains("wal") || l.contains("fsync")
            }
            "cloud_status" => {
                l.contains("Operational") || l.contains("Outage") || l.contains("Incident") || l.contains("Degraded")
            }
            _ => {
                l.starts_with("pub fn ") || l.starts_with("fn ") || l.starts_with("def ") || l.starts_with("func ")
                    || l.starts_with("type ") || l.starts_with("interface ") || l.starts_with("struct ")
            }
        };

        if is_spec_line && doc.signatures.len() < 4 && !doc.signatures.contains(&l.to_string()) {
            doc.signatures.push(l.to_string());
        }

        // 2. Invariants, Panics, Errors, and Failure Modes
        let is_invariant_line = l.contains("panics") || l.contains("Error") || l.contains("invariant") 
            || l.contains("Exception") || l.contains("Breaking") || l.contains("Deprecated") || l.contains("Warning");

        if is_invariant_line && doc.invariants.len() < 3 && !doc.invariants.contains(&l.to_string()) {
            doc.invariants.push(l.to_string());
        }
    }

    // Default invariants if none explicitly matched in raw text
    if doc.signatures.is_empty() {
        doc.signatures.push(format!("symbol: {} (Refer to full interface schema at citation)", symbol));
    }
    if doc.invariants.is_empty() {
        doc.invariants.push("Strict runtime invariants apply; refer to verified official interface.".to_string());
    }

    let elapsed = start.elapsed().as_secs_f64() * 1000.0;
    let wire_dsl = doc.to_dsl();

    Ok(MakoScoutReport {
        query: query.to_string(),
        target_url,
        ecosystem,
        raw_bytes: fetch_res.raw_bytes,
        scrubbed_bytes: fetch_res.scrubbed_bytes,
        reduction_pct: reduction,
        from_cache: fetch_res.from_cache,
        elapsed_ms: elapsed,
        wire_dsl,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_scout_tokio_broadcast() {
        let report = scout_web_documentation("tokio broadcast channel lagged error", false);
        assert!(report.is_ok());
        let rep = report.unwrap();
        assert_eq!(rep.ecosystem, "rust");
        assert!(rep.target_url.contains("tokio/sync/broadcast"));
        assert!(rep.reduction_pct > 80.0 || rep.from_cache);
        assert!(rep.wire_dsl.contains("@api"));
    }
}
