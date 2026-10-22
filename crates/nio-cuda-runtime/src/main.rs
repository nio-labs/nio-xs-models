use anyhow::{Result, anyhow};
use nio_cuda_runtime::{
    format_cuda_prompt, memory_mb, parse_cuda_output, AstMicroEngine, CudaOutput,
};
use std::io::{self, Write};
use std::path::{Path, PathBuf};
use std::time::Instant;
use tokenizers::Tokenizer;

fn parse_cli_args() -> (PathBuf, PathBuf, String, bool, bool) {
    let args: Vec<String> = std::env::args().collect();
    let mut model_path = PathBuf::from("models/nio-cuda-ast.Q4_0.gguf");

    let mut tokenizer_path = PathBuf::from("models/tokenizer.json");

    let mut prompt = "Refactor the authentication handler to use Argon2id instead of bcrypt".to_string();
    let mut is_dag = false;
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
            "--dag" => {
                is_dag = true;
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

    (model_path, tokenizer_path, prompt, is_dag, is_interactive)
}

fn run_single_inference(
    engine: &mut AstMicroEngine,
    tokenizer: &Tokenizer,
    user_query: &str,
    is_dag: bool,
) -> Result<()> {
    engine.reset_cache();

    let formatted_prompt = format_cuda_prompt(user_query, is_dag);
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

    println!("\n⚡ NioCuda Conductor Output (Streaming):");
    println!("--------------------------------------------------");

    let max_gen_tokens = 384;
    let decode_start = Instant::now();

    for step in 0..max_gen_tokens {
        if next_token == eos || next_token == eot {
            break;
        }

        gen_tokens.push(next_token);
        if let Ok(piece) = tokenizer.decode(&[next_token], false) {
            print!("{piece}");
            let _ = io::stdout().flush();
        }

        let step_hidden = engine.forward_stream(&[next_token], prompt_tokens.len() + step)?;
        next_token = engine.next_token(&step_hidden, None)?;
    }

    let decode_duration = decode_start.elapsed();
    let total_gen = gen_tokens.len();
    let gen_tps = if decode_duration.as_secs_f64() > 0.0 {
        total_gen as f64 / decode_duration.as_secs_f64()
    } else {
        0.0
    };

    println!("\n--------------------------------------------------");
    let (final_rss, final_hwm) = memory_mb();
    println!(
        "Decode complete: {total_gen} tokens in {:.1} ms ({:.1} tok/s) | Working RAM: {:.2} MB | Peak: {:.2} MB",
        decode_duration.as_secs_f64() * 1000.0,
        gen_tps,
        final_rss,
        final_hwm
    );

    let full_text = tokenizer
        .decode(&gen_tokens, false)
        .map_err(|e| anyhow!("Decoding failed: {e}"))?;

    match parse_cuda_output(&full_text) {
        CudaOutput::Plan(plan) => {
            println!("\n📋 Parsed CudaPlan (Task: '{}', Goal: '{}'):", plan.task, plan.goal);
            for s in &plan.stages {
                println!(
                    "   • Stage [{}] -> Model: {:<10} Action: {:<16} Target: {}",
                    s.id,
                    s.model,
                    s.action,
                    s.path.as_deref().or(s.file.as_deref()).or(s.cmd.as_deref()).unwrap_or("-")
                );
            }
        }
        CudaOutput::Dag(dag) => {
            println!("\n🕸️ Parsed CudaDag (ID: '{}', Task: '{}'):", dag.id, dag.task);
            for n in &dag.nodes {
                let dep = n.depends_on.as_deref().unwrap_or("ROOT");
                println!(
                    "   • Node [{}] (depends on: {:<6}) -> Model: {:<10} Target: {}",
                    n.id,
                    dep,
                    n.model,
                    n.path.as_deref().or(n.file.as_deref()).or(n.cmd.as_deref()).unwrap_or("-")
                );
            }
        }
        CudaOutput::Text(_) => {}
    }

    Ok(())
}

fn main() -> Result<()> {
    let (model_path, tokenizer_path, prompt, is_dag, is_interactive) = parse_cli_args();

    println!("==================================================");
    println!("⚡ NioCuda AST-Micro Tactical Conductor Runtime");
    println!("==================================================");
    println!("Model:     {}", model_path.display());
    println!("Tokenizer: {}", tokenizer_path.display());

    let (init_rss, init_hwm) = memory_mb();
    println!("Initial RAM: RSS={:.2} MB, Peak={:.2} MB", init_rss, init_hwm);

    if !model_path.exists() {
        return Err(anyhow!(
            "Model file not found at: {}.\nPlease verify path or run training first.",
            model_path.display()
        ));
    }
    if !tokenizer_path.exists() {
        return Err(anyhow!(
            "Tokenizer file not found at: {}.",
            tokenizer_path.display()
        ));
    }

    let t0 = Instant::now();
    let mut engine = AstMicroEngine::new(&model_path)?;
    println!("Engine loaded in {:.2} ms", t0.elapsed().as_secs_f64() * 1000.0);

    let tokenizer = Tokenizer::from_file(&tokenizer_path)
        .map_err(|e| anyhow!("Failed to load tokenizer: {e}"))?;

    let (load_rss, load_hwm) = memory_mb();
    println!("Loaded RAM:  RSS={:.2} MB, Peak={:.2} MB", load_rss, load_hwm);

    if is_interactive {
        println!("\nInteractive Swarm Conductor Console. Type 'exit' to quit.\n");
        let stdin = io::stdin();
        loop {
            print!("nioxs-conductor> ");
            io::stdout().flush()?;
            let mut line = String::new();
            if stdin.read_line(&mut line)? == 0 {
                break;
            }
            let trimmed = line.trim();
            if trimmed.is_empty() {
                continue;
            }
            if trimmed == "exit" || trimmed == "quit" {
                break;
            }
            if let Err(e) = run_single_inference(&mut engine, &tokenizer, trimmed, is_dag) {
                eprintln!("Inference error: {e}");
            }
            println!();
        }
    } else {
        println!("Prompt:    {}", prompt);
        println!("Mode:      {}", if is_dag { "DAG Orchestration" } else { "Sequential Stage Plan" });
        run_single_inference(&mut engine, &tokenizer, &prompt, is_dag)?;
    }

    Ok(())
}
