use anyhow::{Result, anyhow};
use nio_manta_runtime::{
    format_manta_prompt, memory_mb, parse_manta_output, AstMicroEngine, MantaOutput,
};
use std::io::{self, Write};
use std::path::{Path, PathBuf};
use std::time::Instant;
use tokenizers::Tokenizer;

fn parse_cli_args() -> (PathBuf, PathBuf, String, bool, bool) {
    let args: Vec<String> = std::env::args().collect();
    let mut model_path = PathBuf::from("models/nio-manta-ast.Q4_0.gguf");

    let mut tokenizer_path = PathBuf::from("models/tokenizer.json");

    let mut prompt = "Explain the difference between Arc<Mutex<T>> and RwLock<T> in Tokio".to_string();
    let mut is_plan = false;
    let mut is_interactive = false;

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
            "--plan" => {
                is_plan = true;
            }
            "--interactive" | "-i" => {
                is_interactive = true;
            }
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

    (model_path, tokenizer_path, prompt, is_plan, is_interactive)
}

fn run_single_inference(
    engine: &mut AstMicroEngine,
    tokenizer: &Tokenizer,
    user_query: &str,
    is_plan: bool,
) -> Result<()> {
    engine.reset_cache();

    let formatted_prompt = format_manta_prompt(user_query, is_plan);
    let encoding = tokenizer
        .encode(formatted_prompt.as_str(), false)
        .map_err(|e| anyhow!("Tokenization failed: {e}"))?;
    let prompt_tokens = encoding.get_ids().to_vec();

    let prefill_start = Instant::now();
    let hidden = engine.forward_stream(&prompt_tokens, 0)?;
    let prefill_duration = prefill_start.elapsed();

    let (prefill_rss, prefill_hwm) = memory_mb();
    println!(
        "\nPrefill complete in {:.1} ms ({:.1} tok/s) | Working RAM: {:.2} MB | Peak: {:.2} MB",
        prefill_duration.as_secs_f64() * 1000.0,
        prompt_tokens.len() as f64 / prefill_duration.as_secs_f64(),
        prefill_rss,
        prefill_hwm
    );

    let eos: u32 = 151643;
    let eot: u32 = 151645;
    let mut next_token = engine.next_token(&hidden, None)?;
    let mut gen_tokens = Vec::new();
    let mut decode_times = Vec::new();

    let max_gen_tokens = if is_plan { 160 } else { 128 };
    let decode_start = Instant::now();

    for step in 0..max_gen_tokens {
        if next_token == eos || next_token == eot {
            break;
        }

        gen_tokens.push(next_token);

        let t_step = Instant::now();
        let step_hidden = engine.forward_stream(&[next_token], prompt_tokens.len() + step)?;
        next_token = engine.next_token(&step_hidden, None)?;
        decode_times.push(t_step.elapsed().as_secs_f64() * 1000.0);
    }
    let decode_duration = decode_start.elapsed();

    let raw_text = tokenizer
        .decode(&gen_tokens, true)
        .map_err(|e| anyhow!("Detokenization failed: {e}"))?;

    let parsed = parse_manta_output(&raw_text);

    match parsed {
        MantaOutput::Plan(plan) => {
            println!("\n📋 Generated Architectural Plan [ID: {}]:", plan.id);
            for step in &plan.steps {
                let badge = match step.priority.as_str() {
                    "critical" => "🚨 [CRITICAL]",
                    "high" => "⚡ [HIGH]    ",
                    _ => "🔹 [STEP]    ",
                };
                println!("   {} #{}: {}", badge, step.id, step.description);
            }
            for risk in &plan.risks {
                println!("   ⚠️  [{}] {}", risk.level.to_uppercase(), risk.message);
            }
        }
        MantaOutput::Dialogue(text) => {
            println!("\n💬 NioManta Companion:");
            println!("{}", text);
        }
    }

    let tok_per_sec = if !gen_tokens.is_empty() {
        (gen_tokens.len() as f64) / decode_duration.as_secs_f64()
    } else {
        0.0
    };
    let (final_rss, peak_hwm) = memory_mb();

    println!("\n--- Generation Metrics ---");
    println!(
        "Tokens: {} | Decode: {:.2} tok/s ({:.2} ms/token) | Working RAM: {:.2} MB | Peak: {:.2} MB",
        gen_tokens.len(),
        tok_per_sec,
        if !gen_tokens.is_empty() {
            decode_duration.as_secs_f64() * 1000.0 / (gen_tokens.len() as f64)
        } else {
            0.0
        },
        final_rss,
        peak_hwm
    );

    engine.reset_cache();
    Ok(())
}

fn main() -> Result<()> {
    let (model_path, tokenizer_path, prompt, is_plan, is_interactive) = parse_cli_args();

    println!("============================================================");
    println!("🌊 NioManta Companion Runtime (~310M Mobile & Edge AST-µLM)");
    println!("============================================================");

    let (start_rss, start_hwm) = memory_mb();
    println!("Process Start: VmRSS = {:.2} MB | VmHWM = {:.2} MB", start_rss, start_hwm);

    if !model_path.exists() {
        return Err(anyhow!("Model GGUF not found at: {:?}", model_path));
    }
    if !tokenizer_path.exists() {
        return Err(anyhow!("Tokenizer not found at: {:?}", tokenizer_path));
    }

    println!("Loading GGUF: {:?}", model_path);
    let mut engine = AstMicroEngine::new(&model_path)?;
    let tokenizer = Tokenizer::from_file(&tokenizer_path)
        .map_err(|e| anyhow!("Failed to load tokenizer: {e}"))?;

    let (init_rss, init_hwm) = memory_mb();
    println!(
        "Engine Initialized: Working RAM = {:.2} MB | Peak RAM = {:.2} MB\n",
        init_rss, init_hwm
    );

    if is_interactive {
        println!("Type your question below (or 'exit' to quit):\n");
        let stdin = io::stdin();
        loop {
            print!("user> ");
            io::stdout().flush()?;
            let mut line = String::new();
            if stdin.read_line(&mut line)? == 0 {
                break;
            }
            let trimmed = line.trim();
            if trimmed.eq_ignore_ascii_case("exit") || trimmed.eq_ignore_ascii_case("quit") {
                break;
            }
            if trimmed.is_empty() {
                continue;
            }

            let plan_requested = trimmed.starts_with("/plan") || trimmed.starts_with("plan:");
            let clean_query = if plan_requested {
                trimmed.trim_start_matches("/plan").trim_start_matches("plan:").trim()
            } else {
                trimmed
            };

            if let Err(e) = run_single_inference(&mut engine, &tokenizer, clean_query, plan_requested) {
                eprintln!("Error during generation: {e}");
            }
            println!();
        }
    } else {
        run_single_inference(&mut engine, &tokenizer, &prompt, is_plan)?;
    }

    Ok(())
}
