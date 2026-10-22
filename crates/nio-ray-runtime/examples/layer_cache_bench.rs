use candle_core::{IndexOp, Module};
use nio_ray_runtime::{memory_mb, AstMicroEngine, LayerWeights};
use std::path::Path;
use std::time::Instant;

fn cached_forward(
    engine: &mut AstMicroEngine,
    layers: &[LayerWeights],
    tokens: &[u32],
    index_pos: usize,
) -> anyhow::Result<candle_core::Tensor> {
    let mut layer_in = engine.embed(tokens)?;
    for (layer_idx, layer) in layers.iter().enumerate() {
        let cos = engine.cos.clone();
        let sin = engine.sin.clone();
        layer_in = layer.forward(
            &layer_in,
            None,
            index_pos,
            &cos,
            &sin,
            &mut engine.kv_caches[layer_idx],
        )?;
    }
    let out = engine.output_norm.forward(&layer_in)?;
    Ok(out.i((.., tokens.len() - 1, ..))?)
}

fn main() -> anyhow::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    let model_path = args.get(1).map(Path::new).unwrap_or(Path::new("models/nio-ray.Q4_K_M.gguf"));
    let steps: usize = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(8);

    let mut engine = AstMicroEngine::new(model_path)?;
    println!("model: {}", model_path.display());
    println!("layers: {}", engine.block_count);

    let mut layers: Vec<LayerWeights> = Vec::with_capacity(engine.block_count);
    let t_load = Instant::now();
    for i in 0..engine.block_count {
        layers.push(engine.load_layer(i)?);
    }
    let load_ms = t_load.elapsed().as_secs_f64() * 1000.0;
    let (rss_cached, hwm_cached) = memory_mb();
    println!("\nload all {} layers once: {load_ms:.1} ms | RSS {rss_cached:.2} MB | HWM {hwm_cached:.2} MB", layers.len());

    // Warmup both paths
    let _ = engine.forward_stream(&[1u32], 0)?;
    let _ = cached_forward(&mut engine, &layers, &[1u32], 0)?;

    // Path A: current design, reloads every layer on every forward
    engine.reset_cache();
    let t_a = Instant::now();
    for s in 0..steps {
        let _ = engine.forward_stream(&[1u32], s)?;
    }
    let a_ms = t_a.elapsed().as_secs_f64() * 1000.0;

    // Path B: layers cached in RAM
    engine.reset_cache();
    let t_b = Instant::now();
    for s in 0..steps {
        let _ = cached_forward(&mut engine, &layers, &[1u32], s)?;
    }
    let b_ms = t_b.elapsed().as_secs_f64() * 1000.0;

    // next_token cost (full vocab chunked projection)
    let hidden = engine.forward_stream(&[1u32], 0)?;
    let t_c = Instant::now();
    let n = 5;
    for _ in 0..n {
        let _ = engine.next_token(&hidden, None)?;
    }
    let c_ms = t_c.elapsed().as_secs_f64() * 1000.0 / n as f64;

    let (rss_end, hwm_end) = memory_mb();
    println!("\n--- {steps} decode steps ---");
    println!("A reload-per-forward : {:8.2} ms/step  ({:.2} tok/s)", a_ms / steps as f64, 1000.0 / (a_ms / steps as f64));
    println!("B layers cached in RAM: {:8.2} ms/step  ({:.2} tok/s)", b_ms / steps as f64, 1000.0 / (b_ms / steps as f64));
    println!("next_token (vocab proj): {:6.2} ms/call", c_ms);
    println!("\nreload overhead: {:.2} ms/step ({:.0}% of path A)", a_ms / steps as f64 - b_ms / steps as f64, 100.0 * (a_ms - b_ms) / a_ms);
    println!("final RSS {rss_end:.2} MB | HWM {hwm_end:.2} MB");

    Ok(())
}
