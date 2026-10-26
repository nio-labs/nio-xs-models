use anyhow::{anyhow, Result};
use std::str::FromStr;
use tokenizers::Tokenizer;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default, serde::Serialize, serde::Deserialize)]
pub enum ShellDialect {
    #[default]
    Bash,
    Zsh,
    Fish,
    PowerShell,
}

impl FromStr for ShellDialect {
    type Err = anyhow::Error;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.trim().to_lowercase().as_str() {
            "bash" | "sh" | "posix" => Ok(Self::Bash),
            "zsh" => Ok(Self::Zsh),
            "fish" => Ok(Self::Fish),
            "powershell" | "pwsh" | "ps" => Ok(Self::PowerShell),
            other => Err(anyhow!("Unknown shell dialect: '{other}' (expected bash, zsh, fish, or powershell)")),
        }
    }
}

impl std::fmt::Display for ShellDialect {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Bash => write!(f, "bash"),
            Self::Zsh => write!(f, "zsh"),
            Self::Fish => write!(f, "fish"),
            Self::PowerShell => write!(f, "powershell"),
        }
    }
}

impl ShellDialect {
    /// Formatting prefix for neural prompt conditioning
    pub fn prompt_prefix(&self) -> &'static str {
        match self {
            Self::Bash => "[bash]",
            Self::Zsh => "[zsh]",
            Self::Fish => "[fish]",
            Self::PowerShell => "[powershell]",
        }
    }
}

/// Spider Search Hygiene utility for terminal noise suppression and build tree pruning
pub struct SpiderSearchHygiene;

impl SpiderSearchHygiene {
    /// Enrich a search command with spider search hygiene flags (noise suppression, tree exclusion)
    pub fn apply(cmd: &str, shell: ShellDialect) -> String {
        let trimmed = cmd.trim();
        match shell {
            ShellDialect::PowerShell => {
                if trimmed.starts_with("Get-ChildItem") && !trimmed.contains("-Exclude") {
                    format!("{trimmed} -Exclude target,node_modules,.git,.venv")
                } else {
                    trimmed.to_string()
                }
            }
            _ => {
                if trimmed.starts_with("grep") {
                    let mut enriched = trimmed.to_string();
                    if !enriched.contains("-I") && !enriched.contains("-rIn") {
                        enriched = enriched.replacen("grep -rn", "grep -rIn", 1);
                        if !enriched.contains("-rIn") {
                            enriched = enriched.replacen("grep -r", "grep -rIn", 1);
                        }
                    }
                    if !enriched.contains("--exclude-dir") {
                        enriched = format!("{enriched} --exclude-dir={{target,.git,node_modules,dist,.venv}}");
                    }
                    enriched
                } else if trimmed.starts_with("find") && !trimmed.contains("-not -path") {
                    let exclusions = "-not -path '*/.*' -not -path '*/target/*' -not -path '*/node_modules/*'";
                    if trimmed.contains("-type f") {
                        trimmed.replace("-type f", &format!("-type f {exclusions}"))
                    } else if trimmed.starts_with("find .") {
                        trimmed.replacen("find .", &format!("find . {exclusions}"), 1)
                    } else {
                        trimmed.to_string()
                    }
                } else {
                    trimmed.to_string()
                }
            }
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum GrammarState {
    Start,
    TagStart(usize),
    DynamicBody,
    ClosingTag(usize),
    Done,
}

/// Dynamic Grammar Reflex: Enforces structural protocol tags (<viper_cmd>...</viper_cmd>)
/// while delegating token generation dynamically to the neural network without static whitelists.
pub struct DynamicGrammarReflex {
    state: GrammarState,
    shell: ShellDialect,
    tag_start_seq: Vec<u32>,
    tag_end_seq: Vec<u32>,
    eos_ids: Vec<u32>,
    grounded_slot_ids: Vec<u32>,
}

impl DynamicGrammarReflex {
    pub fn new(tokenizer: &Tokenizer) -> Result<Self> {
        Self::new_with_intent_and_shell(tokenizer, "", ShellDialect::Bash)
    }

    pub fn new_with_intent(tokenizer: &Tokenizer, intent: &str) -> Result<Self> {
        Self::new_with_intent_and_shell(tokenizer, intent, ShellDialect::Bash)
    }

    pub fn new_with_intent_and_shell(
        tokenizer: &Tokenizer,
        intent: &str,
        shell: ShellDialect,
    ) -> Result<Self> {
        let vocab_size = tokenizer.get_vocab_size(true) as u32;

        let encode_exact = |s: &str| -> Vec<u32> {
            tokenizer
                .encode(s, false)
                .map(|enc| {
                    enc.get_ids()
                        .iter()
                        .copied()
                        .filter(|&id| id < vocab_size)
                        .collect()
                })
                .unwrap_or_default()
        };

        let mut tag_start_seq = encode_exact("<viper_cmd>");
        if tag_start_seq.is_empty() {
            tag_start_seq = vec![27, 85, 12858, 11684, 29]
                .into_iter()
                .filter(|&id| id < vocab_size)
                .collect();
        }

        let mut tag_end_seq = encode_exact("</viper_cmd>");
        if tag_end_seq.is_empty() {
            tag_end_seq = vec![522, 85, 12858, 11684, 29]
                .into_iter()
                .filter(|&id| id < vocab_size)
                .collect();
        }

        let mut eos_ids = Vec::new();
        if let Some(id) = tokenizer.token_to_id("<|im_end|>") {
            if id < vocab_size {
                eos_ids.push(id);
            }
        }
        if let Some(id) = tokenizer.token_to_id("<|endoftext|>") {
            if id < vocab_size {
                eos_ids.push(id);
            }
        }
        for fallback_eos in [31980, 31978] {
            if fallback_eos < vocab_size && !eos_ids.contains(&fallback_eos) {
                eos_ids.push(fallback_eos);
            }
        }

        // Dynamic slot extraction (ports, literals, numbers) without locking down allowed command verbs
        let mut grounded_slot_ids = Vec::new();
        if !intent.is_empty() {
            for word in intent.split(|c: char| !c.is_alphanumeric() && c != ':' && c != '/') {
                if let Ok(port) = word.parse::<u16>() {
                    for candidate in [format!("{port}"), format!(":{port}")] {
                        for id in encode_exact(&candidate) {
                            if !grounded_slot_ids.contains(&id) {
                                grounded_slot_ids.push(id);
                            }
                        }
                    }
                }
            }
        }

        Ok(Self {
            state: GrammarState::Start,
            shell,
            tag_start_seq,
            tag_end_seq,
            eos_ids,
            grounded_slot_ids,
        })
    }

    pub fn shell(&self) -> ShellDialect {
        self.shell
    }

    pub fn grounded_slots(&self) -> &[u32] {
        &self.grounded_slot_ids
    }

    /// Return allowed candidate token IDs, or None for unconstrained neural generation across full vocabulary
    pub fn allowed_candidates(&self) -> Option<Vec<u32>> {
        match self.state {
            GrammarState::Start => {
                if let Some(&first_tag) = self.tag_start_seq.first() {
                    Some(vec![first_tag])
                } else {
                    None
                }
            }
            GrammarState::TagStart(idx) => {
                if idx < self.tag_start_seq.len() {
                    Some(vec![self.tag_start_seq[idx]])
                } else {
                    None
                }
            }
            // Dynamic body: 100% unconstrained neural selection across entire vocabulary!
            GrammarState::DynamicBody => None,
            GrammarState::ClosingTag(idx) => {
                if idx < self.tag_end_seq.len() {
                    Some(vec![self.tag_end_seq[idx]])
                } else {
                    Some(self.eos_ids.clone())
                }
            }
            GrammarState::Done => Some(self.eos_ids.clone()),
        }
    }

    /// Advance state machine based on generated tokens and decoded text
    pub fn advance(&mut self, token: u32, raw_decoded: &str) {
        if self.state == GrammarState::Done {
            return;
        }

        // Early stopping when tag is reached
        if raw_decoded.contains("</viper_cmd>")
            || raw_decoded.contains("</viper_alert>")
            || raw_decoded.contains("</viper_action>")
        {
            self.state = GrammarState::Done;
            return;
        }

        match self.state {
            GrammarState::Start => {
                if Some(&token) == self.tag_start_seq.first() {
                    if self.tag_start_seq.len() > 1 {
                        self.state = GrammarState::TagStart(1);
                    } else {
                        self.state = GrammarState::DynamicBody;
                    }
                } else {
                    // Started directly with command
                    self.state = GrammarState::DynamicBody;
                }
            }
            GrammarState::TagStart(idx) => {
                if idx + 1 < self.tag_start_seq.len() {
                    self.state = GrammarState::TagStart(idx + 1);
                } else {
                    self.state = GrammarState::DynamicBody;
                }
            }
            GrammarState::DynamicBody => {
                // If the token matches the start of </viper_cmd>, transition to closing tag
                if Some(&token) == self.tag_end_seq.first() {
                    if self.tag_end_seq.len() > 1 {
                        self.state = GrammarState::ClosingTag(1);
                    } else {
                        self.state = GrammarState::Done;
                    }
                } else if raw_decoded.contains('\n') {
                    self.state = GrammarState::Done;
                }
            }
            GrammarState::ClosingTag(idx) => {
                if idx + 1 < self.tag_end_seq.len() {
                    self.state = GrammarState::ClosingTag(idx + 1);
                } else {
                    self.state = GrammarState::Done;
                }
            }
            GrammarState::Done => {}
        }
    }

    pub fn is_done(&self) -> bool {
        self.state == GrammarState::Done
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_shell_dialect_prefixes() {
        assert_eq!(ShellDialect::Bash.prompt_prefix(), "[bash]");
        assert_eq!(ShellDialect::PowerShell.prompt_prefix(), "[powershell]");
        assert_eq!(ShellDialect::Fish.prompt_prefix(), "[fish]");
        assert_eq!(ShellDialect::Zsh.prompt_prefix(), "[zsh]");
    }

    #[test]
    fn test_spider_search_hygiene_grep() {
        let raw = "grep -rn 'TODO' .";
        let clean = SpiderSearchHygiene::apply(raw, ShellDialect::Bash);
        assert!(clean.contains("-rIn"));
        assert!(clean.contains("--exclude-dir={target,.git,node_modules,dist,.venv}"));
    }

    #[test]
    fn test_spider_search_hygiene_powershell() {
        let raw = "Get-ChildItem -Path . -Recurse";
        let clean = SpiderSearchHygiene::apply(raw, ShellDialect::PowerShell);
        assert!(clean.contains("-Exclude target,node_modules,.git,.venv"));
    }
}
