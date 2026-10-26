//! Zero-Key High-Speed Web Crawler and Discovery Engine.
//! Executes keyless HTTP fetching, ETag revalidation, and DuckDuckGo Lite search routing.

use std::process::Command;
use anyhow::{anyhow, Result};
use crate::cache::MakoCache;
use crate::scrubber::scrub_html_content;

pub struct FetchResult {
    pub url: String,
    pub scrubbed_content: String,
    pub raw_bytes: usize,
    pub scrubbed_bytes: usize,
    pub from_cache: bool,
    pub etag: Option<String>,
}

pub struct MakoCrawler {
    cache: MakoCache,
}

impl MakoCrawler {
    pub fn new() -> Result<Self> {
        Ok(Self {
            cache: MakoCache::new()?,
        })
    }

    /// Fetches a live web documentation page with ETag revalidation and LRU caching.
    pub fn fetch_and_scrub(&self, url: &str, force_refresh: bool) -> Result<FetchResult> {
        // 1. Check local cache
        if let Some(cached) = self.cache.get(url, force_refresh) {
            let scrubbed = scrub_html_content(&cached.content);
            return Ok(FetchResult {
                url: url.to_string(),
                raw_bytes: cached.content.len(),
                scrubbed_bytes: scrubbed.len(),
                scrubbed_content: scrubbed,
                from_cache: true,
                etag: cached.etag,
            });
        }

        // 2. Perform live HTTP GET using curl with custom User-Agent and timeouts
        let output = Command::new("curl")
            .arg("-s")
            .arg("-L")
            .arg("-i") // Include response headers to extract ETag
            .arg("--max-time")
            .arg("10")
            .arg("-A")
            .arg("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
            .arg(url)
            .output()
            .map_err(|e| anyhow!("Failed to execute curl network fetch: {e}"))?;

        if !output.status.success() {
            return Err(anyhow!("Network fetch failed for URL: {}", url));
        }

        let raw_response = String::from_utf8_lossy(&output.stdout);
        
        // 3. Separate headers and body
        let (headers_part, body_part) = if let Some(sep_idx) = raw_response.find("\r\n\r\n") {
            (&raw_response[..sep_idx], &raw_response[sep_idx + 4..])
        } else if let Some(sep_idx) = raw_response.find("\n\n") {
            (&raw_response[..sep_idx], &raw_response[sep_idx + 2..])
        } else {
            ("", raw_response.as_ref())
        };

        // Extract ETag if present
        let mut etag = None;
        for line in headers_part.lines() {
            if line.to_lowercase().starts_with("etag:") {
                etag = Some(line[5..].trim().trim_matches('"').to_string());
                break;
            }
        }

        let raw_len = body_part.len();
        let scrubbed = scrub_html_content(body_part);
        let scrubbed_len = scrubbed.len();

        // 4. Save to local cache
        let _ = self.cache.put(url, etag.clone(), None, body_part.to_string());

        Ok(FetchResult {
            url: url.to_string(),
            scrubbed_content: scrubbed,
            raw_bytes: raw_len,
            scrubbed_bytes: scrubbed_len,
            from_cache: false,
            etag,
        })
    }

    /// Keyless Search Fallback using DuckDuckGo Lite (Zero API key required).
    pub fn search_duckduckgo_lite(&self, query: &str) -> Result<Vec<String>> {
        let clean_query = query.replace(' ', "+");
        let search_url = format!("https://html.duckduckgo.com/html/?q={clean_query}");

        let output = Command::new("curl")
            .arg("-s")
            .arg("-L")
            .arg("--max-time")
            .arg("8")
            .arg("-A")
            .arg("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            .arg(&search_url)
            .output()
            .map_err(|e| anyhow!("DuckDuckGo keyless search failed: {e}"))?;

        let body = String::from_utf8_lossy(&output.stdout);
        let mut links = Vec::new();

        // Extract outbound result links from DuckDuckGo HTML
        for line in body.lines() {
            if line.contains("class=\"result__url\"") || line.contains("class=\"result__snippet\"") {
                if let Some(href_start) = line.find("href=\"//duckduckgo.com/l/?uddg=") {
                    let after = &line[href_start + 32..];
                    if let Some(end_idx) = after.find('&') {
                        let encoded_url = &after[..end_idx];
                        if let Ok(decoded) = urlencoding_decode(encoded_url) {
                            if !decoded.contains("duckduckgo.com") && !links.contains(&decoded) {
                                links.push(decoded);
                            }
                        }
                    }
                }
            }
        }

        Ok(links)
    }
}

fn urlencoding_decode(input: &str) -> Result<String> {
    let mut out = String::with_capacity(input.len());
    let bytes = input.as_bytes();
    let mut i = 0;
    while i < bytes.len() {
        if bytes[i] == b'%' && i + 2 < bytes.len() {
            if let Ok(val) = u8::from_str_radix(std::str::from_utf8(&bytes[i+1..i+3])?, 16) {
                out.push(val as char);
                i += 3;
                continue;
            }
        }
        out.push(bytes[i] as char);
        i += 1;
    }
    Ok(out)
}
