use anyhow::{Result, anyhow};
pub use nio_ray_runtime::{AstMicroEngine, memory_mb};
use std::path::{Path, PathBuf};
use std::time::Instant;
use tokenizers::Tokenizer;

pub mod grammar;
pub use grammar::{DynamicGrammarReflex, ShellDialect, SpiderSearchHygiene};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ViperOutput {
    Command(String),
    Alert { level: String, message: String },
    Raw(String),
}

#[derive(Debug, Clone)]
pub struct ViperExecutionTelemetry {
    pub raw_text: String,
    pub output: ViperOutput,
    pub shell: ShellDialect,
    pub tokens: usize,
    pub tps: f64,
    pub avg_step_ms: f64,
    pub prefill_ms: f64,
    pub rss_init: f64,
    pub rss_working: f64,
    pub hwm_peak: f64,
}

pub fn find_default_viper_paths() -> Option<(PathBuf, PathBuf)> {
    let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
    let home_model = format!("{}/.nioxs/models/viper.Q4_0.gguf", home);
    let home_model_ast = format!("{}/.nioxs/models/nio-viper-ast.Q4_0.gguf", home);
    let home_tok = format!("{}/.nioxs/models/viper-tokenizer.json", home);
    let home_tok_ast = format!("{}/.nioxs/models/nio-viper-tokenizer.json", home);

    let model_candidates = [
        "models/viper.Q4_0.gguf",
        "models/nio-viper-ast.Q4_0.gguf",
        "models/nio-viper/viper.Q4_0.gguf",
        "../../models/nio-viper/viper.Q4_0.gguf",
        "../models/nio-viper/viper.Q4_0.gguf",
        home_model.as_str(),
        home_model_ast.as_str(),
    ];
    let tok_candidates = [
        "models/viper-tokenizer.json",
        "models/nio-viper-tokenizer.json",
        "models/nio-viper/viper-tokenizer.json",
        "../../models/nio-viper/viper-tokenizer.json",
        "../models/nio-viper/viper-tokenizer.json",
        home_tok.as_str(),
        home_tok_ast.as_str(),
    ];

    for m in &model_candidates {
        let mp = PathBuf::from(m);
        if mp.exists() {
            for t in &tok_candidates {
                let tp = PathBuf::from(t);
                if tp.exists() {
                    return Some((mp, tp));
                }
            }
        }
    }
    None
}

pub fn execute_viper_ast(
    user_query: &str,
    model_path: &Path,
    tokenizer_path: &Path,
    is_ast: bool,
    max_tokens: usize,
) -> Result<ViperExecutionTelemetry> {
    execute_viper_ast_with_shell(user_query, model_path, tokenizer_path, is_ast, max_tokens, ShellDialect::Bash)
}

pub fn execute_viper_ast_with_shell(
    user_query: &str,
    model_path: &Path,
    tokenizer_path: &Path,
    is_ast: bool,
    max_tokens: usize,
    shell: ShellDialect,
) -> Result<ViperExecutionTelemetry> {
    let tokenizer = Tokenizer::from_file(tokenizer_path).map_err(|e| {
        anyhow!(
            "Failed to load tokenizer from {}: {e}",
            tokenizer_path.display()
        )
    })?;

    let mut engine = AstMicroEngine::new(model_path).map_err(|e| {
        anyhow!(
            "Failed to load GGUF model from {}: {e}",
            model_path.display()
        )
    })?;

    let (rss_init, _) = memory_mb();

    let prompt_prefix = match shell {
        ShellDialect::PowerShell => format!("<|im_start|>user\n[powershell] {}<|im_end|>\n<|im_start|>assistant\n", user_query),
        ShellDialect::Fish => format!("<|im_start|>user\n[fish] {}<|im_end|>\n<|im_start|>assistant\n", user_query),
        ShellDialect::Zsh => format!("<|im_start|>user\n[zsh] {}<|im_end|>\n<|im_start|>assistant\n", user_query),
        ShellDialect::Bash => format!("<|im_start|>user\n{}<|im_end|>\n<|im_start|>assistant\n", user_query),
    };

    let encoding = tokenizer.encode(prompt_prefix.as_str(), false).map_err(|e| anyhow!("{e}"))?;
    let prompt_tokens = encoding.get_ids().to_vec();

    let t_pref = Instant::now();
    let hidden = engine.forward_stream(&prompt_tokens, 0)?;
    let prefill_ms = t_pref.elapsed().as_secs_f64() * 1000.0;

    let mut eos_tokens = Vec::new();
    if let Some(id) = tokenizer.token_to_id("<|im_end|>") {
        eos_tokens.push(id);
    }
    if let Some(id) = tokenizer.token_to_id("<|endoftext|>") {
        eos_tokens.push(id);
    }
    for fallback in [31980, 31978] {
        if !eos_tokens.contains(&fallback) {
            eos_tokens.push(fallback);
        }
    }

    let mut grammar = if is_ast {
        Some(DynamicGrammarReflex::new_with_intent_and_shell(&tokenizer, user_query, shell)?)
    } else {
        None
    };

    let first_cands = grammar.as_ref().and_then(|g| g.allowed_candidates());
    let mut next = engine.next_token(&hidden, first_cands.as_deref())?;
    let mut generated = Vec::new();
    let mut decode_times = Vec::new();

    for step in 0..max_tokens {
        if eos_tokens.contains(&next) {
            break;
        }
        generated.push(next);
        let current_text = tokenizer.decode(&generated, false).unwrap_or_default();

        // 1. Immediate early stopping on closing tags
        if current_text.contains("</viper_cmd>")
            || current_text.contains("</viper_alert>")
            || current_text.contains("</viper_action>")
            || current_text.contains("</viper_review>")
        {
            break;
        }

        // 2. Repetition tripwire
        let len = generated.len();
        if len >= 3 && generated[len - 1] == generated[len - 2] && generated[len - 2] == generated[len - 3] {
            break;
        }

        // 3. Command completion on newline
        if current_text.contains('\n') && (current_text.len() > 10) {
            break;
        }

        if let Some(ref mut g) = grammar {
            g.advance(next, &current_text);
            if g.is_done() {
                break;
            }
        }

        let t_step = Instant::now();
        let step_hidden = engine.forward_stream(&[next], prompt_tokens.len() + step)?;
        let step_cands = grammar.as_ref().and_then(|g| g.allowed_candidates());
        next = engine.next_token(&step_hidden, step_cands.as_deref())?;
        decode_times.push(t_step.elapsed().as_secs_f64() * 1000.0);
    }

    let raw_text = tokenizer.decode(&generated, false).unwrap_or_default();
    let parsed = parse_viper_output_with_shell(&raw_text, shell);

    let (rss_end, hwm_end) = memory_mb();
    let avg_step_ms: f64 = if !decode_times.is_empty() {
        decode_times.iter().sum::<f64>() / decode_times.len() as f64
    } else {
        0.0
    };
    let gen_tps = if avg_step_ms > 0.0 { 1000.0 / avg_step_ms } else { 0.0 };

    Ok(ViperExecutionTelemetry {
        raw_text,
        output: parsed,
        shell,
        tokens: generated.len(),
        tps: gen_tps,
        avg_step_ms,
        prefill_ms,
        rss_init,
        rss_working: rss_end,
        hwm_peak: hwm_end,
    })
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

/// Parse structured output from NioViper with default Bash dialect
pub fn parse_viper_output(text: &str) -> ViperOutput {
    parse_viper_output_with_shell(text, ShellDialect::Bash)
}

/// Parse structured output with target shell dialect and apply Spider Search Hygiene
pub fn parse_viper_output_with_shell(text: &str, shell: ShellDialect) -> ViperOutput {
    if let Some(cmd) = extract_viper_cmd(text) {
        let hygienic_cmd = SpiderSearchHygiene::apply(&cmd, shell);
        ViperOutput::Command(hygienic_cmd)
    } else if let Some((level, message)) = extract_viper_alert(text) {
        ViperOutput::Alert { level, message }
    } else {
        let clean = text.trim().trim_start_matches('_').trim();
        let known_verbs = [
            "ss", "lsof", "fuser", "kill", "pkill", "find", "docker",
            "cargo", "git", "systemctl", "journalctl", "ps", "grep", "cat", "awk", "curl", "tar",
            "ls", "pwd", "mkdir", "df", "free", "resolvectl", "rsync", "kubectl",
            "Get-Process", "Stop-Process", "Get-ChildItem", "Select-String", "Get-NetTCPConnection",
            "status", "count", "string", "pidof",
        ];
        if known_verbs.iter().any(|v| clean.starts_with(v)) {
            let first_line = clean.lines().next().unwrap_or(clean).trim();
            let hygienic_cmd = SpiderSearchHygiene::apply(first_line, shell);
            ViperOutput::Command(hygienic_cmd)
        } else {
            ViperOutput::Raw(text.to_string())
        }
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
        "Get-Process Stop-Process Get-ChildItem Select-String -Exclude ",
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

    #[test]
    fn test_parse_viper_output_reflex() {
        let text = "_ss -tlpn | xargs kill -9";
        assert_eq!(
            parse_viper_output(text),
            ViperOutput::Command("ss -tlpn | xargs kill -9".to_string())
        );
    }

    #[test]
    fn test_parse_viper_search_hygiene_application() {
        let text = "<viper_cmd>grep -rn 'API_KEY' .</viper_cmd>";
        let parsed = parse_viper_output_with_shell(text, ShellDialect::Bash);
        match parsed {
            ViperOutput::Command(cmd) => {
                assert!(cmd.contains("-rIn"), "Should inject -rIn: {cmd}");
                assert!(cmd.contains("--exclude-dir="), "Should inject exclusion: {cmd}");
            }
            _ => panic!("Expected command output"),
        }
    }
}
