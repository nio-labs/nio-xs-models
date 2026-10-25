use serde::{Deserialize, Serialize};
use std::env;

#[derive(Debug, Serialize, Deserialize)]
pub struct DecisionOutput {
    pub model: String,
    pub input: String,
    pub decision: String,
    pub sentiment: String,
    pub score: f32,
    pub confidence: f32,
    pub is_safe: bool,
}

fn main() -> anyhow::Result<()> {
    let args: Vec<String> = env::args().collect();
    let query = if args.len() > 1 {
        args[1..].join(" ")
    } else {
        "git status".to_string()
    };

    println!("NioMicro Runtime CLI v0.3.0 (Local Engine)");
    println!("Evaluating: \"{}\"", query);

    // Heuristic & Decision layer check
    let is_destructive = query.contains("rm -rf")
        || query.contains("--force")
        || query.contains("DROP DATABASE")
        || query.contains("AWS_SECRET_KEY")
        || query.contains("sk_live_");

    let verdict = if is_destructive {
        DecisionOutput {
            model: "nioxs::micro".into(),
            input: query,
            decision: "reject".into(),
            sentiment: "negative".into(),
            score: 0.02,
            confidence: 0.99,
            is_safe: false,
        }
    } else {
        DecisionOutput {
            model: "nioxs::micro".into(),
            input: query,
            decision: "approve".into(),
            sentiment: "positive".into(),
            score: 0.98,
            confidence: 0.97,
            is_safe: true,
        }
    };

    let json = serde_json::to_string_pretty(&verdict)?;
    println!("{}", json);

    Ok(())
}
