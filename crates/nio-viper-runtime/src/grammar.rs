use anyhow::Result;
use std::collections::HashMap;
use tokenizers::Tokenizer;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum GrammarState {
    Start,
    CommandVerb,
    Arguments,
    PipedVerb,
    ClosingTag,
    Done,
}

pub struct DynamicGrammarReflex {
    state: GrammarState,
    tag_start_ids: Vec<u32>,
    verb_ids: Vec<u32>,
    arg_tokens_by_verb: HashMap<String, Vec<u32>>,
    pipe_ids: Vec<u32>,
    tag_end_ids: Vec<u32>,
    eos_ids: Vec<u32>,
    all_arg_ids: Vec<u32>,
    current_verb: Option<String>,
    token_to_text: HashMap<u32, String>,
}

impl DynamicGrammarReflex {
    pub fn new(tokenizer: &Tokenizer) -> Result<Self> {
        let mut token_to_text = HashMap::new();
        for id in 0..tokenizer.get_vocab_size(true) as u32 {
            if let Some(text) = tokenizer.id_to_token(id) {
                token_to_text.insert(id, text);
            }
        }

        let encode_exact = |s: &str| -> Vec<u32> {
            tokenizer.encode(s, false).map(|enc| enc.get_ids().to_vec()).unwrap_or_default()
        };

        let tag_start_ids = encode_exact("<viper_cmd>");
        let tag_end_ids = encode_exact("</viper_cmd>");

        let mut eos_ids = Vec::new();
        if let Some(id) = tokenizer.token_to_id("<|im_end|>") {
            eos_ids.push(id);
        }
        if let Some(id) = tokenizer.token_to_id("<|endoftext|>") {
            eos_ids.push(id);
        }

        let verbs = [
            "lsof", "fuser", "ss", "kill", "pkill", "find", "grep", "cat", "awk",
            "docker", "cargo", "git", "systemctl", "journalctl", "ps", "curl", "tar", "sed",
        ];

        let mut verb_ids = Vec::new();
        for v in &verbs {
            for id in encode_exact(v) {
                if !verb_ids.contains(&id) {
                    verb_ids.push(id);
                }
            }
        }

        let mut arg_tokens_by_verb = HashMap::new();
        let verb_rules: &[(&str, &[&str])] = &[
            ("lsof", &[" -ti:", " -i:", " -i :", "3000", "8080", "5432", "4000", " | xargs kill -9", " | kill -9"]),
            ("fuser", &[" -k ", "3000/tcp", "8080/tcp", "5432/tcp", "4000/tcp", " -n tcp "]),
            ("ss", &[" -tulpn", " -tlpn", " -ta", " -tl", " -s", " | grep :"]),
            ("kill", &[" -9 ", " -15 ", "$(lsof -t -i:", "3000)", "8080)"]),
            ("pkill", &[" -9 -f ", " -f "]),
            ("find", &[" . -type f", " . -name ", " -size +100M", " -size +50M", " -mtime 0", " -mtime -1", " -exec rm -f {} +", " -exec du -h {} + | sort -hr", " | xargs wc -l"]),
            ("docker", &[" ps -a", " system prune -af", " compose up -d", " compose down", " rm -f $(docker ps -aq)", " logs -f "]),
            ("git", &[" status", " diff", " stash pop", " checkout -b ", " reset --hard HEAD", " branch -D ", " log -n 5 --oneline"]),
            ("cargo", &[" check --locked", " test --lib", " clippy --all-targets", " build --release", " clean -p "]),
            ("systemctl", &[" restart ", " status ", " stop ", " daemon-reload", "nginx", "docker"]),
            ("journalctl", &[" -u ", " -xe", " -f", " --no-pager"]),
        ];

        let mut all_arg_ids = Vec::new();
        for &(v, patterns) in verb_rules {
            let mut ids = Vec::new();
            for pat in patterns {
                for id in encode_exact(pat) {
                    if !ids.contains(&id) {
                        ids.push(id);
                    }
                    if !all_arg_ids.contains(&id) {
                        all_arg_ids.push(id);
                    }
                }
            }
            arg_tokens_by_verb.insert(v.to_string(), ids);
        }

        let pipe_patterns = [" | grep ", " | awk '{print $1}'", " | xargs kill -9", " | sort -hr", " | uniq -c"];
        let mut pipe_ids = Vec::new();
        for pat in &pipe_patterns {
            for id in encode_exact(pat) {
                if !pipe_ids.contains(&id) {
                    pipe_ids.push(id);
                }
            }
        }

        Ok(Self {
            state: GrammarState::Start,
            tag_start_ids,
            verb_ids,
            arg_tokens_by_verb,
            pipe_ids,
            tag_end_ids,
            eos_ids,
            all_arg_ids,
            current_verb: None,
            token_to_text,
        })
    }

    /// Return allowed token candidates for the current grammar state
    pub fn allowed_candidates(&self) -> &[u32] {
        match self.state {
            GrammarState::Start => &self.tag_start_ids,
            GrammarState::CommandVerb => &self.verb_ids,
            GrammarState::Arguments => {
                if let Some(ref verb) = self.current_verb {
                    if let Some(verb_args) = self.arg_tokens_by_verb.get(verb) {
                        return verb_args.as_slice();
                    }
                }
                &self.all_arg_ids
            }
            GrammarState::PipedVerb => {
                if !self.pipe_ids.is_empty() {
                    &self.pipe_ids
                } else {
                    &self.verb_ids
                }
            }
            GrammarState::ClosingTag => &self.tag_end_ids,
            GrammarState::Done => &self.eos_ids,
        }
    }

    /// Advance the grammar state machine based on the accepted token
    pub fn advance(&mut self, token: u32, raw_decoded: &str) {
        if self.tag_start_ids.contains(&token) || raw_decoded.contains("<viper_cmd>") {
            if self.state == GrammarState::Start {
                self.state = GrammarState::CommandVerb;
                return;
            }
        }

        if self.state == GrammarState::CommandVerb {
            if let Some(text) = self.token_to_text.get(&token) {
                let clean = text.trim();
                for verb in self.arg_tokens_by_verb.keys() {
                    if clean.contains(verb) {
                        self.current_verb = Some(verb.clone());
                        break;
                    }
                }
            }
            self.state = GrammarState::Arguments;
            return;
        }

        if self.state == GrammarState::Arguments {
            if raw_decoded.ends_with('|') || raw_decoded.ends_with("| ") {
                self.state = GrammarState::PipedVerb;
                return;
            }
            // After arguments are emitted (or command length exceeded), transition to closing tag
            if raw_decoded.len() > 15 || raw_decoded.contains("kill -9") || raw_decoded.contains("-tulpn") || raw_decoded.contains("prune -af") {
                self.state = GrammarState::ClosingTag;
                return;
            }
        }

        if self.state == GrammarState::PipedVerb {
            self.state = GrammarState::Arguments;
            return;
        }

        if self.state == GrammarState::ClosingTag {
            self.state = GrammarState::Done;
        }
    }

    pub fn is_done(&self) -> bool {
        self.state == GrammarState::Done
    }
}
