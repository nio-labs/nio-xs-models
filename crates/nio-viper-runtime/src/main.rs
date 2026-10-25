use anyhow::{Result, anyhow};
use nio_viper_runtime::{
    AstMicroEngine, memory_mb, parse_viper_output, DynamicGrammarReflex, ViperOutput,
};
use std::path::{Path, PathBuf};
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

fn parse_cli_args() -> (PathBuf, PathBuf, String, bool) {
    let args: Vec<String> = std::env::args().collect();
    let mut model_path = find_default_path(&[
        "models/nio-viper/viper.Q4_0.gguf",
        "../../models/nio-viper/viper.Q4_0.gguf",
        "models/viper.Q4_0.gguf",
        "models/nio-viper-ast.Q4_0.gguf",
    ]);
    let mut tokenizer_path = find_default_path(&[
        "models/nio-viper/viper-tokenizer.json",
        "../../models/nio-viper/viper-tokenizer.json",
        "models/viper-tokenizer.json",
        "models/nio-viper-tokenizer.json",
    ]);
    let mut prompt = "Kill whatever process is listening on port 3000".to_string();
    let mut is_ast = true; // Tactical AST candidate slicing is default for Viper

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
            "--ast" => {
                is_ast = true;
            }
            "--unconstrained" | "--no-ast" => {
                is_ast = false;
            }
            "--viper" => {
                // Compatibility flag
            }
            arg if !arg.starts_with("--") => {
                // If first positional argument and looks like a path, use as model
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

    (model_path, tokenizer_path, prompt, is_ast)
}

fn main() -> Result<()> {
    println!("=== NioViper AST-µLM Tactical Striker Runtime ===");
    let (model_path, tokenizer_path, user_query, is_ast) = parse_cli_args();

    let (rss0, hwm0) = memory_mb();
    println!("Process Start: VmRSS = {:.2} MB | VmHWM = {:.2} MB", rss0, hwm0);

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
        "Engine Initialized ({} layers, {} vocab): VmRSS = {:.2} MB | VmHWM = {:.2} MB",
        engine.block_count, engine.vocab_size, rss_init, hwm_init
    );

    let prompt = format!(
        "<|im_start|>user\n{}<|im_end|>\n<|im_start|>assistant\n",
        user_query
    );
    println!("\nPrompt: {}", user_query);

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

    let eos = tokenizer.token_to_id("<|im_end|>").unwrap_or(31980);
    let eot = tokenizer.token_to_id("<|endoftext|>").unwrap_or(151643);

    let mut grammar = if is_ast {
        println!("Mode: Dynamic AST Grammar Reflex (Sub-20µs Sampling, < 25MB RAM)");
        Some(DynamicGrammarReflex::new(&tokenizer)?)
    } else {
        println!("Mode: Chunked Streaming Unconstrained Projection");
        None
    };

    let first_cands = grammar.as_ref().map(|g| g.allowed_candidates());
    let mut next = engine.next_token(&hidden, first_cands)?;
    let mut generated = Vec::new();
    let mut decode_times = Vec::new();

    print!("Generated Raw: ");
    std::io::Write::flush(&mut std::io::stdout())?;

    for step in 0..48 {
        if next == eos || next == eot {
            break;
        }
        generated.push(next);
        let text = tokenizer.decode(&[next], false).unwrap_or_default();
        print!("{}", text);
        std::io::Write::flush(&mut std::io::stdout())?;

        let current_text = tokenizer.decode(&generated, false).unwrap_or_default();
        if let Some(ref mut g) = grammar {
            g.advance(next, &current_text);
            if g.is_done() {
                break;
            }
        }

        let t_step = Instant::now();
        let step_hidden = engine.forward_stream(&[next], prompt_tokens.len() + step)?;
        let step_cands = grammar.as_ref().map(|g| g.allowed_candidates());
        next = engine.next_token(&step_hidden, step_cands)?;
        decode_times.push(t_step.elapsed().as_secs_f64() * 1000.0);
    }
    println!();

    let raw_text = tokenizer.decode(&generated, false).unwrap_or_default();
    let parsed = parse_viper_output(&raw_text);

    println!("\n=== Structured Tactical Output ===");
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
    println!("Tokens: {}", generated.len());
    println!("Speed: {:.2} tok/s ({:.2} ms/token)", gen_tps, avg_step_ms);
    println!("Initial RAM: {:.2} MB", rss_init);
    println!("Working RAM: {:.2} MB", rss_end);
    println!("Peak RAM: {:.2} MB", hwm_end);

    Ok(())
}
