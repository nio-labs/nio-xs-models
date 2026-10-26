//! LLM-Native Wire DSL Parser and Generator for Mako (150M).
//! Compresses sprawling documentation into ultra-dense, typed interface schemas for parent LLMs.

use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct MakoWireDoc {
    pub target_api: String,
    pub ecosystem: String,
    pub signatures: Vec<String>,
    pub invariants: Vec<String>,
    pub next_hops: Vec<String>,
    pub citation_url: String,
}

impl MakoWireDoc {
    pub fn new(target_api: &str, ecosystem: &str, citation_url: &str) -> Self {
        Self {
            target_api: target_api.to_string(),
            ecosystem: ecosystem.to_string(),
            signatures: Vec::new(),
            invariants: Vec::new(),
            next_hops: Vec::new(),
            citation_url: citation_url.to_string(),
        }
    }

    pub fn to_dsl(&self) -> String {
        let mut out = Vec::new();
        out.push(format!("@api {} [ecosystem: {}]", self.target_api, self.ecosystem));

        for sig in &self.signatures {
            out.push(sig.clone());
        }

        for inv in &self.invariants {
            out.push(format!("[INVARIANT]: {}", inv));
        }

        if !self.next_hops.is_empty() {
            out.push(format!("[NEXT_HOPS]: {}", self.next_hops.join(", ")));
        }

        out.push(format!("[CITATION]: {}", self.citation_url));
        out.join("\n")
    }

    pub fn parse_dsl(dsl_text: &str) -> Option<Self> {
        let lines: Vec<&str> = dsl_text.lines().map(|l| l.trim()).filter(|l| !l.is_empty()).collect();
        if lines.is_empty() || !lines[0].starts_with("@api") {
            return None;
        }

        let first = lines[0];
        let mut target_api = String::new();
        let mut ecosystem = "unknown".to_string();

        if let Some(rest) = first.strip_prefix("@api ") {
            if let Some(bracket_idx) = rest.find('[') {
                target_api = rest[..bracket_idx].trim().to_string();
                let meta = &rest[bracket_idx..];
                if let Some(eco_start) = meta.find("ecosystem:") {
                    let eco_val = &meta[eco_start + 10..];
                    ecosystem = eco_val.trim_end_matches(']').trim().to_string();
                }
            } else {
                target_api = rest.trim().to_string();
            }
        }

        let mut signatures = Vec::new();
        let mut invariants = Vec::new();
        let mut next_hops = Vec::new();
        let mut citation_url = String::new();

        for &line in &lines[1..] {
            if let Some(inv) = line.strip_prefix("[INVARIANT]: ") {
                invariants.push(inv.to_string());
            } else if let Some(hops) = line.strip_prefix("[NEXT_HOPS]: ") {
                for h in hops.split(',') {
                    next_hops.push(h.trim().to_string());
                }
            } else if let Some(cit) = line.strip_prefix("[CITATION]: ") {
                citation_url = cit.to_string();
            } else if !line.starts_with('[') {
                signatures.push(line.to_string());
            }
        }

        Some(Self {
            target_api,
            ecosystem,
            signatures,
            invariants,
            next_hops,
            citation_url,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_wire_dsl_roundtrip() {
        let mut doc = MakoWireDoc::new("tokio::sync::broadcast", "rust", "https://docs.rs/tokio");
        doc.signatures.push("fn channel<T: Clone>(cap: usize) -> (Sender<T>, Receiver<T>) !cap==0:panics".to_string());
        doc.invariants.push("Bounded multi-producer, multi-consumer. Drops lagged messages.".to_string());
        doc.next_hops.push("https://docs.rs/tokio/struct.Sender.html".to_string());

        let dsl = doc.to_dsl();
        assert!(dsl.contains("@api tokio::sync::broadcast"));
        assert!(dsl.contains("[INVARIANT]: Bounded"));

        let parsed = MakoWireDoc::parse_dsl(&dsl).unwrap();
        assert_eq!(parsed.target_api, "tokio::sync::broadcast");
        assert_eq!(parsed.ecosystem, "rust");
        assert_eq!(parsed.signatures.len(), 1);
        assert_eq!(parsed.invariants.len(), 1);
    }
}
