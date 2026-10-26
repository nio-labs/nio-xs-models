//! CLI Binary for Mako (150M) Web Intelligence & Documentation Scout.

use std::env;
use anyhow::Result;
use nio_mako_runtime::{scout_web_documentation, MakoCache};

fn print_usage() {
    println!("Mako (150M) Web Intelligence & Documentation Scout Runtime");
    println!("Usage: nioxs-mako [OPTIONS] <QUERY>\n");
    println!("Options:");
    println!("  --force-refresh, -f   Bypass local cache and force live web network fetch");
    println!("  --clean-cache         Purge all locally cached documentation");
    println!("  --json                Output result in JSON format");
    println!("  --help, -h            Show this help message\n");
    println!("Examples:");
    println!("  nioxs-mako 'how to handle tokio broadcast lagged error in rust'");
    println!("  nioxs-mako 'AbortController timeout in typescript' --force-refresh");
    println!("  nioxs-mako 'asyncio.TaskGroup exceptiongroup python'");
}

fn main() -> Result<()> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        print_usage();
        return Ok(());
    }

    let mut force_refresh = false;
    let mut json_output = false;
    let mut query_parts = Vec::new();

    for arg in &args[1..] {
        match arg.as_str() {
            "--help" | "-h" => {
                print_usage();
                return Ok(());
            }
            "--clean-cache" => {
                let cache = MakoCache::new()?;
                let count = cache.clean()?;
                println!("✅ Purged {} cached documentation items.", count);
                return Ok(());
            }
            "--force-refresh" | "-f" => {
                force_refresh = true;
            }
            "--json" => {
                json_output = true;
            }
            other => {
                query_parts.push(other);
            }
        }
    }

    if query_parts.is_empty() {
        eprintln!("Error: No query provided.");
        print_usage();
        std::process::exit(1);
    }

    let query = query_parts.join(" ");
    let report = scout_web_documentation(&query, force_refresh)?;

    if json_output {
        println!("{}", serde_json::to_string_pretty(&report)?);
    } else {
        println!("============================================================");
        println!("🦈 Mako (150M) Web Documentation Scout Report");
        println!("============================================================");
        println!("Query:        {}", report.query);
        println!("Target URL:   {}", report.target_url);
        println!("Ecosystem:    {}", report.ecosystem);
        println!("Payload:      {} raw bytes -> {} scrubbed bytes ({:.1}% reduction)", 
                 report.raw_bytes, report.scrubbed_bytes, report.reduction_pct);
        println!("Latency:      {:.2} ms (from cache: {})", report.elapsed_ms, report.from_cache);
        println!("------------------------------------------------------------");
        println!("LLM-Native Wire DSL Schema:\n");
        println!("{}", report.wire_dsl);
        println!("============================================================");
    }

    Ok(())
}
