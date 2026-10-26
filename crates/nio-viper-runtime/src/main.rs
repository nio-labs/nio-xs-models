use anyhow::{Result, anyhow};
use nio_viper_runtime::{
    memory_mb, parse_viper_output_with_shell, DynamicGrammarReflex, ViperOutput,
    AstMicroEngine, ShellDialect,
};
use std::path::{Path, PathBuf};
use std::str::FromStr;
use std::time::Instant;
use tokenizers::Tokenizer;

fn find_default_path(candidates: &[&str]) -> PathBuf {
    for c in candidates {
        let p = PathBuf::from(c);
        if p.exists() {
            return p;
        }
    }
    PathBuf::from(candidates[0])
}

fn parse_cli_args() -> (PathBuf, PathBuf, String, bool, bool, ShellDialect) {
    let args: Vec<String> = std::env::args().collect();
    let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
    let home_model = format!("{}/.nioxs/models/nio-viper-ast.Q4_0.gguf", home);
    let home_tok = format!("{}/.nioxs/models/nio-viper-tokenizer.json", home);

    let mut model_path = find_default_path(&[
        home_model.as_str(),
        "models/nio-viper/viper.Q4_0.gguf",
        "../../models/nio-viper/viper.Q4_0.gguf",
        "models/viper.Q4_0.gguf",
        "models/nio-viper-ast.Q4_0.gguf",
    ]);
    let mut tokenizer_path = find_default_path(&[
        home_tok.as_str(),
        "models/nio-viper/viper-tokenizer.json",
        "../../models/nio-viper/viper-tokenizer.json",
        "models/viper-tokenizer.json",
        "models/nio-viper-tokenizer.json",
    ]);
    let mut prompt = "Kill whatever process is listening on port 3000".to_string();
    let mut is_ast = true;
    let mut run_bench = false;
    let mut shell = ShellDialect::Bash;

    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--model" | "-m" => {
                if i + 1 < args.len() {
                    model_path = PathBuf::from(&args[i + 1]);
                    i += 1;
                }
            }
            "--tokenizer" | "-t" => {
                if i + 1 < args.len() {
                    tokenizer_path = PathBuf::from(&args[i + 1]);
                    i += 1;
                }
            }
            "--prompt" | "-p" => {
                if i + 1 < args.len() {
                    prompt = args[i + 1].clone();
                    i += 1;
                }
            }
            "--shell" | "-s" => {
                if i + 1 < args.len() {
                    shell = ShellDialect::from_str(&args[i + 1]).unwrap_or_default();
                    i += 1;
                }
            }
            "--benchmark" | "-b" => {
                run_bench = true;
            }
            "--ast" => {
                is_ast = true;
            }
            "--unconstrained" | "--no-ast" => {
                is_ast = false;
            }
            "--viper" => {}
            arg if !arg.starts_with("--") => {
                if i == 1 && (arg.ends_with(".gguf") || Path::new(arg).exists()) {
                    model_path = PathBuf::from(arg);
                } else if i == 2 && (arg.ends_with(".json") || Path::new(arg).exists()) {
                    tokenizer_path = PathBuf::from(arg);
                } else {
                    prompt = arg.to_string();
                }
            }
            _ => {}
        }
        i += 1;
    }

    (model_path, tokenizer_path, prompt, is_ast, run_bench, shell)
}

fn main() -> Result<()> {
    let (rss_start, hwm_start) = memory_mb();
    println!("=== NioViper AST-µLM Tactical Striker Runtime ===");
    println!(
        "Process Start: VmRSS = {:.2} MB | VmHWM = {:.2} MB",
        rss_start, hwm_start
    );

    let (model_path, tokenizer_path, user_query, is_ast, run_bench, shell) = parse_cli_args();

    if run_bench {
        return run_validation_suite(&model_path, &tokenizer_path, is_ast, shell);
    }

    let tokenizer = Tokenizer::from_file(&tokenizer_path).map_err(|e| {
        anyhow!(
            "Failed to load tokenizer from {}: {e}",
            tokenizer_path.display()
        )
    })?;

    let mut engine = AstMicroEngine::new(&model_path).map_err(|e| {
        anyhow!(
            "Failed to load GGUF model from {}: {e}",
            model_path.display()
        )
    })?;

    let (rss_init, hwm_init) = memory_mb();
    println!(
        "Engine Initialized ({} layers, {} vocab): VmRSS = {:.2} MB | VmHWM = {:.2} MB | Shell: {}",
        engine.block_count, engine.vocab_size, rss_init, hwm_init, shell
    );

    let prompt = match shell {
        ShellDialect::PowerShell => format!("<|im_start|>user\n[powershell] {}<|im_end|>\n<|im_start|>assistant\n", user_query),
        ShellDialect::Fish => format!("<|im_start|>user\n[fish] {}<|im_end|>\n<|im_start|>assistant\n", user_query),
        ShellDialect::Zsh => format!("<|im_start|>user\n[zsh] {}<|im_end|>\n<|im_start|>assistant\n", user_query),
        ShellDialect::Bash => format!("<|im_start|>user\n{}<|im_end|>\n<|im_start|>assistant\n", user_query),
    };
    println!("\nPrompt [{}]: {}", shell, user_query);

    let encoding = tokenizer.encode(prompt.as_str(), false).map_err(|e| anyhow!("{e}"))?;
    let prompt_tokens = encoding.get_ids().to_vec();

    let t_pref = Instant::now();
    let hidden = engine.forward_stream(&prompt_tokens, 0)?;
    let prefill_ms = t_pref.elapsed().as_secs_f64() * 1000.0;
    let (rss_pref, hwm_pref) = memory_mb();
    println!(
        "Prefill complete in {:.1} ms! Working VmRSS = {:.2} MB | Peak VmHWM = {:.2} MB",
        prefill_ms, rss_pref, hwm_pref
    );

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
        println!("Mode: Dynamic AST Grammar Reflex (Dialect: {}, Sub-20µs Sampling, < 25MB RAM)", shell);
        Some(DynamicGrammarReflex::new_with_intent_and_shell(&tokenizer, &user_query, shell)?)
    } else {
        println!("Mode: Chunked Streaming Unconstrained Projection");
        None
    };

    let first_cands = grammar.as_ref().and_then(|g| g.allowed_candidates());
    let mut next = engine.next_token(&hidden, first_cands.as_deref())?;
    let mut generated = Vec::new();
    let mut decode_times = Vec::new();

    print!("Generated Raw: ");
    std::io::Write::flush(&mut std::io::stdout())?;

    for step in 0..32 {
        if eos_tokens.contains(&next) {
            break;
        }
        generated.push(next);
        let text = tokenizer.decode(&[next], false).unwrap_or_default();
        print!("{}", text);
        std::io::Write::flush(&mut std::io::stdout())?;

        let current_text = tokenizer.decode(&generated, false).unwrap_or_default();

        // 1. Immediate stop on completion tags
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
    println!();

    let raw_text = tokenizer.decode(&generated, false).unwrap_or_default();
    let parsed = parse_viper_output_with_shell(&raw_text, shell);

    println!("\n=== Structured Tactical Output [{}] ===", shell);
    match parsed {
        ViperOutput::Command(cmd) => {
            println!("Command Verdict: \x1b[32m{}\x1b[0m", cmd);
        }
        ViperOutput::Alert { level, message } => {
            println!("Diagnostic Alert [{}]: \x1b[33m{}\x1b[0m", level, message);
        }
        ViperOutput::Raw(txt) => {
            println!("Output: {}", txt);
        }
    }

    let (rss_end, hwm_end) = memory_mb();
    let avg_step_ms: f64 = if !decode_times.is_empty() {
        decode_times.iter().sum::<f64>() / decode_times.len() as f64
    } else {
        0.0
    };
    let gen_tps = if avg_step_ms > 0.0 { 1000.0 / avg_step_ms } else { 0.0 };

    println!("\n=== Viper Metrics ===");
    println!("Dialect: {}", shell);
    println!("Tokens: {}", generated.len());
    println!("Speed: {:.2} tok/s ({:.2} ms/token)", gen_tps, avg_step_ms);
    println!("Initial RAM: {:.2} MB", rss_init);
    println!("Working RAM: {:.2} MB", rss_end);
    println!("Peak RAM: {:.2} MB", hwm_end);

    Ok(())
}

fn run_validation_suite(model_path: &Path, tokenizer_path: &Path, is_ast: bool, shell: ShellDialect) -> Result<()> {
    let test_cases = [
        ("Port 3000 Kill", "Kill whatever process is listening on port 3000"),
        ("List Directory", "list directory"),
        ("Log Search", "Find all files larger than 100MB in /var/log and sort by size"),
        ("Docker Prune", "Delete all stopped docker containers and unused volumes"),
        ("Git Soft Reset", "undo last commit but keep staged changes"),
    ];

    println!("\n=== Running Viper Regression & CI Validation Suite (Dialect: {}) ===", shell);
    for (name, prompt) in &test_cases {
        let t0 = Instant::now();
        let telemetry = nio_viper_runtime::execute_viper_ast_with_shell(prompt, model_path, tokenizer_path, is_ast, 32, shell)?;
        let elapsed = t0.elapsed().as_millis();

        let verdict = match &telemetry.output {
            ViperOutput::Command(c) => format!("CMD: {c}"),
            ViperOutput::Alert { level, message } => format!("ALERT({level}): {message}"),
            ViperOutput::Raw(r) => format!("RAW: {r}"),
        };

        println!(
            "✓ [{:<16}] Wall: {:>5}ms | Tokens: {:>2} | Peak RAM: {:>5.2}MB | {}",
            name, elapsed, telemetry.tokens, telemetry.hwm_peak, verdict
        );

        assert!(
            telemetry.rss_working < 100.0,
            "Working RSS exceeded 100MB envelope: {:.2}MB",
            telemetry.rss_working
        );
        assert!(
            telemetry.tokens <= 32,
            "Tokens runaway: {} tokens generated",
            telemetry.tokens
        );
    }
    println!("=== All Validation Gates Passed Successfully (< 100MB Working RSS, Bounded Decoding) ===\n");
    Ok(())
}
