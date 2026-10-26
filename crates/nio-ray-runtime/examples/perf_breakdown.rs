use nio_ray_runtime::{memory_mb, AstMicroEngine};
use std::path::Path;
use std::time::Instant;
use tokenizers::Tokenizer;

fn main() -> anyhow::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    let model_path = args.get(1).map(Path::new).unwrap_or(Path::new("models/nio-ray.Q4_K_M.gguf"));
    let tok_path = args.get(2).map(Path::new).unwrap_or(Path::new("models/tokenizer.json"));

    println!("=== 1. PER-REQUEST ENGINE INIT (what every HTTP chat request pays) ===");
    for i in 0..3 {
        let t = Instant::now();
        let tokenizer = Tokenizer::from_file(tok_path).map_err(|e| anyhow::anyhow!("{e}"))?;
        let t_tok = t.elapsed();
        let t2 = Instant::now();
        let engine = AstMicroEngine::new(model_path)?;
        let t_model = t2.elapsed();
        let (rss, hwm) = memory_mb();
        println!(
            "  run {i}: tokenizer {:>7.1} ms | engine(mmap+gguf parse) {:>7.1} ms | total {:>7.1} ms | RSS {rss:.1} MB | HWM {hwm:.1} MB",
            t_tok.as_secs_f64() * 1000.0,
            t_model.as_secs_f64() * 1000.0,
            t.elapsed().as_secs_f64() * 1000.0,
        );
        drop(engine);
        drop(tokenizer);
    }

    println!("\n=== 2. PREFILL COST vs PROMPT SIZE ===");
    let tokenizer = Tokenizer::from_file(tok_path).map_err(|e| anyhow::anyhow!("{e}"))?;
    let mut engine = AstMicroEngine::new(model_path)?;
    for n in [16usize, 64, 256, 512, 1024, 2048] {
        let text = "write me hello world in php. ".repeat(n);
        let ids = tokenizer.encode(text.as_str(), false).map_err(|e| anyhow::anyhow!("{e}"))?.get_ids().to_vec();
        engine.reset_cache();
        let t = Instant::now();
        let hidden = engine.forward_stream(&ids, 0)?;
        let prefill = t.elapsed().as_secs_f64() * 1000.0;
        let t2 = Instant::now();
        let _ = engine.next_token(&hidden, None)?;
        let proj = t2.elapsed().as_secs_f64() * 1000.0;
        println!(
            "  {n:>5} prompts -> {:>5} tokens | prefill {:>8.1} ms ({:>6.1} ms/tok) | +next_token {:>7.1} ms",
            ids.len(),
            prefill,
            prefill / ids.len() as f64,
            proj
        );
    }

    println!("\n=== 3. PER-DECODE-TOKEN COST ===");
    engine.reset_cache();
    let hidden = engine.forward_stream(&[1u32], 0)?;
    let steps = 6;
    let t = Instant::now();
    for _ in 0..steps {
        let _ = engine.next_token(&hidden, None)?;
    }
    println!("  next_token (full 151936-vocab projection): {:>7.1} ms/token", t.elapsed().as_secs_f64() * 1000.0 / steps as f64);

    let t = Instant::now();
    for s in 0..steps {
        let _ = engine.forward_stream(&[1u32], s)?;
    }
    println!("  forward_stream (reload 24 layers):        {:>7.1} ms/token", t.elapsed().as_secs_f64() * 1000.0 / steps as f64);

    let (rss, hwm) = memory_mb();
    println!("\nfinal RSS {rss:.2} MB | HWM {hwm:.2} MB");
    Ok(())
}
