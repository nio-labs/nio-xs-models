//! JSONL benchmark driver for released NioRay weights using CPU Candle kernels.
use anyhow::{Result, anyhow, ensure};
use candle_core::{Device, Tensor, quantized::gguf_file};
use candle_transformers::{generation::LogitsProcessor, models::quantized_qwen2::ModelWeights};
use serde::Deserialize;
use serde_json::json;
use std::{
    fs::File,
    io::{self, BufRead, Write},
    time::Instant,
};
use tokenizers::Tokenizer;

#[derive(Deserialize)]
struct Request {
    task_id: String,
    prompt: String,
    max_tokens: usize,
    #[serde(default)]
    prompt_tokens: Option<usize>,
    #[serde(default)]
    ignore_eos: bool,
    #[serde(default)]
    stop: Vec<String>,
}

fn memory() -> serde_json::Value {
    let status = std::fs::read_to_string("/proc/self/status").unwrap_or_default();
    let field = |name: &str| -> Option<u64> {
        status
            .lines()
            .find(|line| line.starts_with(name))?
            .split_whitespace()
            .nth(1)?
            .parse()
            .ok()
    };
    json!({"rss_kib": field("VmRSS:"), "peak_rss_kib": field("VmHWM:")})
}

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    ensure!(
        args.len() == 4,
        "usage: nioray-benchmark MODEL TOKENIZER THREADS < requests.jsonl"
    );
    let threads: usize = args[3].parse()?;
    rayon::ThreadPoolBuilder::new()
        .num_threads(threads)
        .build_global()?;
    let process_start = Instant::now();
    let tokenizer = Tokenizer::from_file(&args[2]).map_err(|e| anyhow!("{e}"))?;
    let mut file = File::open(&args[1])?;
    let content = gguf_file::Content::read(&mut file)?;
    let tokens = content
        .metadata
        .get("tokenizer.ggml.tokens")
        .ok_or_else(|| anyhow!("missing vocabulary"))?
        .to_vec()?;
    let vocabulary_size = tokens.len();
    let vocab = tokenizer.get_vocab(true);
    for (token, id) in &vocab {
        ensure!(
            tokens.get(*id as usize).and_then(|v| v.to_string().ok()) == Some(token),
            "tokenizer mismatch at {id}"
        );
    }
    for (id, token) in tokens.iter().enumerate() {
        let token = token.to_string()?;
        ensure!(
            token.starts_with("[PAD") || vocab.get(token) == Some(&(id as u32)),
            "missing model token {id}"
        );
    }
    let device = Device::Cpu;
    let mut model = ModelWeights::from_gguf(content, &mut file, &device)?;
    let load_ms = process_start.elapsed().as_secs_f64() * 1000.;
    let mut out = io::BufWriter::new(io::stdout().lock());
    writeln!(
        out,
        "{}",
        json!({"type":"load", "model":args[1], "tokenizer":args[2], "threads":threads,
        "load_ms":load_ms, "vocabulary_size":vocabulary_size, "memory":memory(),
        "runtime":"candle-core/candle-transformers 0.8.4 CPU", "sampling":"greedy argmax"})
    )?;
    out.flush()?;
    let eos = tokenizer
        .token_to_id("<|im_end|>")
        .ok_or_else(|| anyhow!("missing ChatML EOS"))?;
    let eot = tokenizer
        .token_to_id("<|endoftext|>")
        .ok_or_else(|| anyhow!("missing EOT"))?;
    for line in io::stdin().lock().lines() {
        let request: Request = serde_json::from_str(&line?)?;
        ensure!(request.max_tokens > 0, "max_tokens must be positive");
        let start = Instant::now();
        let encoded = tokenizer
            .encode(request.prompt.as_str(), false)
            .map_err(|e| anyhow!("{e}"))?;
        let mut prompt = encoded.get_ids().to_vec();
        if let Some(length) = request.prompt_tokens {
            ensure!(
                prompt.len() >= length,
                "source prompt shorter than requested length"
            );
            prompt.truncate(length);
        }
        ensure!(!prompt.is_empty(), "empty prompt");
        let tokenization_ms = start.elapsed().as_secs_f64() * 1000.;
        let input = Tensor::new(prompt.as_slice(), &device)?.unsqueeze(0)?;
        let prefill_start = Instant::now();
        let logits = model.forward(&input, 0)?.squeeze(0)?; // index zero resets KV cache
        let prefill_ms = prefill_start.elapsed().as_secs_f64() * 1000.;
        let mut sampler = LogitsProcessor::new(0, None, None);
        let mut next = sampler.sample(&logits)?;
        let ttft_ms = start.elapsed().as_secs_f64() * 1000.;
        let decode_start = Instant::now();
        let mut generated = Vec::new();
        let mut decode_steps = 0;
        let mut stop_reason = "length";
        let mut text = String::new();
        for index in 0..request.max_tokens {
            if !request.ignore_eos && (next == eos || next == eot) {
                stop_reason = "eos";
                break;
            }
            generated.push(next);
            if !request.stop.is_empty() {
                text = tokenizer
                    .decode(&generated, false)
                    .map_err(|e| anyhow!("{e}"))?;
                if request.stop.iter().any(|stop| text.contains(stop)) {
                    stop_reason = "stop_string";
                    break;
                }
            }
            if index + 1 < request.max_tokens {
                let input = Tensor::new(&[next], &device)?.unsqueeze(0)?;
                let logits = model.forward(&input, prompt.len() + index)?.squeeze(0)?;
                next = sampler.sample(&logits)?;
                decode_steps += 1;
            }
        }
        let decode_ms = decode_start.elapsed().as_secs_f64() * 1000.;
        let total_ms = start.elapsed().as_secs_f64() * 1000.;
        if request.stop.is_empty() {
            text = tokenizer
                .decode(&generated, false)
                .map_err(|e| anyhow!("{e}"))?;
        }
        let raw_text = text.clone();
        if stop_reason == "stop_string" {
            if let Some(index) = request.stop.iter().filter_map(|stop| text.find(stop)).min() {
                text.truncate(index);
            }
        }
        writeln!(
            out,
            "{}",
            json!({"type":"sample", "task_id":request.task_id,
            "prompt_tokens":prompt.len(), "generated_tokens":generated.len(), "decode_steps":decode_steps,
            "max_tokens":request.max_tokens, "ignore_eos":request.ignore_eos,
            "tokenization_ms":tokenization_ms, "prefill_ms":prefill_ms, "ttft_ms":ttft_ms,
            "decode_ms":decode_ms, "decode_tokens_per_second":decode_steps as f64/(decode_ms/1000.),
            "total_ms":total_ms, "stop_reason":stop_reason, "text":text, "raw_text":raw_text,
            "generated_ids":generated, "memory":memory()})
        )?;
        out.flush()?;
    }
    Ok(())
}
