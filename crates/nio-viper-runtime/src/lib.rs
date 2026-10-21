use anyhow::{Result, anyhow};
pub use nio_ray_runtime::{AstMicroEngine, memory_mb};
use tokenizers::Tokenizer;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ViperOutput {
    Command(String),
    Alert { level: String, message: String },
    Raw(String),
}

/// Extract `<viper_cmd>...</viper_cmd>` tags from model output
pub fn extract_viper_cmd(text: &str) -> Option<String> {
    let start_tag = "<viper_cmd>";
    let end_tag = "</viper_cmd>";
    if let Some(start_idx) = text.find(start_tag) {
        let content_start = start_idx + start_tag.len();
        if let Some(end_idx) = text[content_start..].find(end_tag) {
            return Some(text[content_start..content_start + end_idx].trim().to_string());
        } else {
            return Some(text[content_start..].trim().to_string());
        }
    }
    None
}

/// Extract `<viper_alert level='...'>...</viper_alert>` tags from model output
pub fn extract_viper_alert(text: &str) -> Option<(String, String)> {
    let start_tag = "<viper_alert";
    let end_tag = "</viper_alert>";
    if let Some(start_idx) = text.find(start_tag) {
        let rest = &text[start_idx..];
        let tag_close = rest.find('>')?;
        let tag_header = &rest[..tag_close];
        let level = if let Some(lvl_idx) = tag_header.find("level='") {
            let lvl_rest = &tag_header[lvl_idx + 7..];
            let lvl_end = lvl_rest.find('\'').unwrap_or(lvl_rest.len());
            lvl_rest[..lvl_end].to_string()
        } else if let Some(lvl_idx) = tag_header.find("level=\"") {
            let lvl_rest = &tag_header[lvl_idx + 7..];
            let lvl_end = lvl_rest.find('"').unwrap_or(lvl_rest.len());
            lvl_rest[..lvl_end].to_string()
        } else {
            "info".to_string()
        };

        let content_start = start_idx + tag_close + 1;
        let message = if let Some(end_idx) = text[content_start..].find(end_tag) {
            text[content_start..content_start + end_idx].trim().to_string()
        } else {
            text[content_start..].trim().to_string()
        };

        return Some((level, message));
    }
    None
}

/// Parse structured output from NioViper
pub fn parse_viper_output(text: &str) -> ViperOutput {
    if let Some(cmd) = extract_viper_cmd(text) {
        ViperOutput::Command(cmd)
    } else if let Some((level, message)) = extract_viper_alert(text) {
        ViperOutput::Alert { level, message }
    } else {
        ViperOutput::Raw(text.to_string())
    }
}

/// Generate candidate token IDs for tactical shell commands and XML tags
pub fn tactical_candidates(tokenizer: &Tokenizer) -> Result<Vec<u32>> {
    let tactical_samples = concat!(
        "<viper_cmd></viper_cmd><viper_alert level='error' level='warn'></viper_alert>",
        "lsof -ti: kill -9 xargs | grep awk sort find -name -size +100M -exec ",
        "docker ps -a rm -f systemctl restart status journalctl -u -xe ",
        "git status diff checkout branch -D stash pop add commit -m push origin ",
        "cargo check --locked test --lib clippy run --release build ",
        "error[E0382]: use of moved value borrows mutably cannot borrow ",
        "cat /var/log/nginx/access.log | awk '{print $1}' | sort | uniq -c | sort -nr ",
        "\n / - _ : = \" ' ` ; & && || $ () {} [] 0 1 2 3 4 5 6 7 8 9"
    );

    let enc = tokenizer.encode(tactical_samples, false).map_err(|e| anyhow!("{e}"))?;
    let mut pool = enc.get_ids().to_vec();

    if let Some(im_end) = tokenizer.token_to_id("<|im_end|>") {
        pool.push(im_end);
    }
    if let Some(eot) = tokenizer.token_to_id("<|endoftext|>") {
        pool.push(eot);
    }

    pool.sort_unstable();
    pool.dedup();
    Ok(pool)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_extract_viper_cmd() {
        let text = "<viper_cmd>lsof -ti:3000 | xargs kill -9</viper_cmd>";
        assert_eq!(extract_viper_cmd(text), Some("lsof -ti:3000 | xargs kill -9".to_string()));
    }

    #[test]
    fn test_extract_viper_alert() {
        let text = "<viper_alert level='error'>error[E0382]: use of moved value `data`</viper_alert>";
        assert_eq!(
            extract_viper_alert(text),
            Some(("error".to_string(), "error[E0382]: use of moved value `data`".to_string()))
        );
    }
}
