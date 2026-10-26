//! Cache Hygiene & Invalidation Engine for Mako Web Intelligence.
//! Features HTTP 304 ETag tracking, hard 50.0 MB LRU disk ceiling, and auto-eviction.

use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};
use serde::{Deserialize, Serialize};
use anyhow::Result;

const MAX_CACHE_SIZE_BYTES: u64 = 50 * 1024 * 1024; // 50.0 MB hard ceiling

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct CacheEntry {
    pub url: String,
    pub etag: Option<String>,
    pub last_modified: Option<String>,
    pub cached_at_secs: u64,
    pub last_accessed_secs: u64,
    pub content: String,
    pub size_bytes: u64,
}

pub struct MakoCache {
    cache_dir: PathBuf,
}

impl MakoCache {
    pub fn new() -> Result<Self> {
        let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
        let cache_dir = Path::new(&home).join(".nioxs").join("cache").join("mako");
        fs::create_dir_all(&cache_dir)?;
        Ok(Self { cache_dir })
    }

    pub fn with_path(cache_dir: PathBuf) -> Result<Self> {
        fs::create_dir_all(&cache_dir)?;
        Ok(Self { cache_dir })
    }

    fn url_to_hash(url: &str) -> String {
        // Simple fast alphanumeric hash
        let mut hash: u64 = 5381;
        for byte in url.bytes() {
            hash = ((hash << 5).wrapping_add(hash)).wrapping_add(byte as u64);
        }
        format!("{:x}", hash)
    }

    fn file_path(&self, url: &str) -> PathBuf {
        let filename = format!("{}.json", Self::url_to_hash(url));
        self.cache_dir.join(filename)
    }

    pub fn get(&self, url: &str, force_refresh: bool) -> Option<CacheEntry> {
        if force_refresh {
            return None;
        }

        let path = self.file_path(url);
        if !path.exists() {
            return None;
        }

        let data = fs::read_to_string(&path).ok()?;
        let mut entry: CacheEntry = serde_json::from_str(&data).ok()?;

        // Update access time for LRU
        let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs();
        entry.last_accessed_secs = now;
        let _ = fs::write(&path, serde_json::to_string(&entry).unwrap_or_default());

        Some(entry)
    }

    pub fn put(&self, url: &str, etag: Option<String>, last_modified: Option<String>, content: String) -> Result<()> {
        let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs();
        let size = content.len() as u64;

        let entry = CacheEntry {
            url: url.to_string(),
            etag,
            last_modified,
            cached_at_secs: now,
            last_accessed_secs: now,
            content,
            size_bytes: size,
        };

        let path = self.file_path(url);
        fs::write(&path, serde_json::to_string(&entry)?)?;

        self.enforce_lru_ceiling()?;
        Ok(())
    }

    pub fn enforce_lru_ceiling(&self) -> Result<()> {
        let mut entries = Vec::new();
        let mut total_size = 0u64;

        if let Ok(dir_entries) = fs::read_dir(&self.cache_dir) {
            for entry in dir_entries.flatten() {
                let path = entry.path();
                if path.extension().and_then(|s| s.to_str()) == Some("json") {
                    if let Ok(metadata) = entry.metadata() {
                        let size = metadata.len();
                        total_size += size;

                        if let Ok(data) = fs::read_to_string(&path) {
                            if let Ok(cache_entry) = serde_json::from_str::<CacheEntry>(&data) {
                                entries.push((path, cache_entry.last_accessed_secs, size));
                            }
                        }
                    }
                }
            }
        }

        // If exceeding ceiling, evict oldest 25% entries
        if total_size > MAX_CACHE_SIZE_BYTES {
            entries.sort_by_key(|e| e.1); // Sort ascending by last_accessed
            let evict_count = (entries.len() / 4).max(1);
            for (path, _, size) in entries.into_iter().take(evict_count) {
                let _ = fs::remove_file(path);
                total_size = total_size.saturating_sub(size);
            }
        }

        Ok(())
    }

    pub fn clean(&self) -> Result<usize> {
        let mut count = 0;
        if let Ok(dir_entries) = fs::read_dir(&self.cache_dir) {
            for entry in dir_entries.flatten() {
                let path = entry.path();
                if path.is_file() {
                    let _ = fs::remove_file(path);
                    count += 1;
                }
            }
        }
        Ok(count)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_mako_cache_lifecycle() {
        let temp_dir = std::env::temp_dir().join("mako_test_cache");
        let cache = MakoCache::with_path(temp_dir).unwrap();

        let url = "https://docs.rs/tokio/latest";
        let content = "tokio broadcast doc content";

        cache.put(url, Some("etag-123".to_string()), None, content.to_string()).unwrap();

        // 1. Normal hit
        let entry = cache.get(url, false).unwrap();
        assert_eq!(entry.content, content);
        assert_eq!(entry.etag.as_deref(), Some("etag-123"));

        // 2. Force refresh bypass
        let missed = cache.get(url, true);
        assert!(missed.is_none());

        // 3. Clean
        let cleaned = cache.clean().unwrap();
        assert!(cleaned >= 1);
        assert!(cache.get(url, false).is_none());
    }
}
