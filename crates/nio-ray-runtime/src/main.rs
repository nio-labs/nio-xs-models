use anyhow::{Result, anyhow};
use nio_ray_runtime::{AstMicroEngine, memory_mb};
use std::path::Path;
use std::time::Instant;
use tokenizers::Tokenizer;

fn main() -> Result<()> {
    println!("=== NioRay AST-µLM Streaming Reflex Runtime ===");
    let args: Vec<String> = std::env::args().collect();
    let model_path = if args.len() > 1 {
        Path::new(&args[1])
    } else {
        Path::new("models/nio-ray-ast.Q4_0.gguf")
    };
    let tokenizer_path = if args.len() > 2 {
        Path::new(&args[2])
    } else {
        Path::new("models/tokenizer.json")
    };

    let (rss0, hwm0) = memory_mb();
    println!("Process Start: VmRSS = {:.2} MB | VmHWM = {:.2} MB", rss0, hwm0);

    let tokenizer = Tokenizer::from_file(tokenizer_path).map_err(|e| anyhow!("{e}"))?;
    let mut engine = AstMicroEngine::new(model_path)?;
    let (rss_init, hwm_init) = memory_mb();
    println!("Engine Initialized: VmRSS = {:.2} MB | VmHWM = {:.2} MB", rss_init, hwm_init);

    let prompt = if args.len() > 3 {
        args[3].clone()
    } else {
        "<|im_start|>user\nWrite a hello world in Rust.<|im_end|>\n<|im_start|>assistant\n".to_string()
    };

    println!("\nPrompt:\n{}", prompt);
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

    let eos = tokenizer.token_to_id("<|im_end|>").unwrap_or(151645);
    let eot = tokenizer.token_to_id("<|endoftext|>").unwrap_or(151643);

    let mut next = engine.next_token(&hidden, None)?;
    let mut generated = Vec::new();
    let mut decode_times = Vec::new();

    print!("Generated: ");
    std::io::Write::flush(&mut std::io::stdout())?;

    for step in 0..64 {
        if next == eos || next == eot {
            break;
        }
        generated.push(next);
        let text = tokenizer.decode(&[next], false).unwrap_or_default();
        print!("{}", text);
        std::io::Write::flush(&mut std::io::stdout())?;

        let t_step = Instant::now();
        let step_hidden = engine.forward_stream(&[next], prompt_tokens.len() + step)?;
        next = engine.next_token(&step_hidden, None)?;
        decode_times.push(t_step.elapsed().as_secs_f64() * 1000.0);
    }
    println!();

    let (rss_end, hwm_end) = memory_mb();
    let avg_step_ms: f64 = if !decode_times.is_empty() {
        decode_times.iter().sum::<f64>() / decode_times.len() as f64
    } else {
        0.0
    };
    let gen_tps = if avg_step_ms > 0.0 { 1000.0 / avg_step_ms } else { 0.0 };

    println!("\n=== Metrics ===");
    println!("Tokens: {}", generated.len());
    println!("Speed: {:.2} tok/s ({:.2} ms/token)", gen_tps, avg_step_ms);
    println!("Initial RAM: {:.2} MB", rss_init);
    println!("Working RAM: {:.2} MB", rss_end);
    println!("Peak RAM: {:.2} MB", hwm_end);

    Ok(())
}
