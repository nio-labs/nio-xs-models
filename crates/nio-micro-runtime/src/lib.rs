use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DecisionVerdict {
    pub model: String,
    pub input: String,
    pub decision: String,
    pub sentiment: String,
    pub score: f32,
    pub confidence: f32,
    pub is_safe: bool,
}

pub struct NioMicro {
    pub model_name: String,
}

impl NioMicro {
    pub fn new() -> Self {
        Self {
            model_name: "nioxs::micro".to_string(),
        }
    }

    pub fn evaluate(&self, text: &str) -> DecisionVerdict {
        let text_lower = text.to_lowercase();
        
        let is_unsafe = text_lower.contains("rm -rf")
            || text_lower.contains("drop database")
            || text_lower.contains("force push")
            || text_lower.contains("--force")
            || text_lower.contains("aws_secret_key")
            || text_lower.contains("sk_live_")
            || text_lower.contains("chmod 777")
            || text_lower.contains("pickle.loads");

        let is_negative_sentiment = text_lower.contains("garbage")
            || text_lower.contains("toxic")
            || text_lower.contains("hate")
            || text_lower.contains("terrible");

        if is_unsafe {
            DecisionVerdict {
                model: self.model_name.clone(),
                input: text.to_string(),
                decision: "reject".into(),
                sentiment: "negative".into(),
                score: 0.02,
                confidence: 0.99,
                is_safe: false,
            }
        } else if is_negative_sentiment {
            DecisionVerdict {
                model: self.model_name.clone(),
                input: text.to_string(),
                decision: "reject".into(),
                sentiment: "negative".into(),
                score: 0.15,
                confidence: 0.95,
                is_safe: false,
            }
        } else {
            DecisionVerdict {
                model: self.model_name.clone(),
                input: text.to_string(),
                decision: "approve".into(),
                sentiment: "positive".into(),
                score: 0.96,
                confidence: 0.98,
                is_safe: true,
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_safe_approve() {
        let micro = NioMicro::new();
        let res = micro.evaluate("git status");
        assert_eq!(res.decision, "approve");
        assert!(res.is_safe);
        assert!(res.score > 0.9);
    }

    #[test]
    fn test_unsafe_reject() {
        let micro = NioMicro::new();
        let res = micro.evaluate("rm -rf / --no-preserve-root");
        assert_eq!(res.decision, "reject");
        assert!(!res.is_safe);
        assert!(res.score < 0.1);
    }
}
