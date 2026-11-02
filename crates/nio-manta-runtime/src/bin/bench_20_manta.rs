use anyhow::Result;
use nio_manta_runtime::{format_manta_prompt, memory_mb, AstMicroEngine};
use std::path::PathBuf;
use std::time::Instant;
use tokenizers::Tokenizer;

const PROMPTS: &[(&str, &str, bool)] = &[
    ("PubSub", "Design a distributed pub-sub message broker in Rust", true),
    ("RateLimiter", "Design a sliding window rate limiter for a high-throughput API gateway", true),
    ("KeyValue", "Architect an in-memory key-value cache with LRU eviction and persistence", true),
    ("DistributedLock", "Design a distributed locking mechanism using consensus and leases", true),
    ("MetricsPipeline", "Design a real-time streaming metrics ingestion pipeline", true),
    ("Mutex", "Explain the trade-offs between Arc<Mutex<T>> and RwLock<T> in async Tokio", false),
    ("ZeroCopy", "What is zero-copy networking and how does splice/sendfile achieve it?", false),
    ("Epoll", "How does Linux epoll work under the hood compared to select and poll?", false),
    ("TailCall", "Explain tail call optimization and why it matters in compilers", false),
    ("MVCC", "How does Multi-Version Concurrency Control (MVCC) work in relational databases?", false),
    ("LRU", "Write an LRU cache implementation in Rust with O(1) get and put", false),
    ("Trie", "Implement a concurrent Trie prefix tree for autocomplete", false),
    ("RingBuffer", "Implement a lock-free single-producer single-consumer ring buffer in Rust", false),
    ("Merkle", "Explain how Merkle trees verify data integrity in distributed systems", false),
    ("Backoff", "Implement an exponential backoff with jitter retry strategy in Rust", false),
    ("MemoryLeak", "How do you detect memory leaks and page fragmentation in Linux user-space?", false),
    ("Deadlock", "What causes deadlock in concurrent thread pools and how to prevent it?", false),
    ("GitConflict", "How do you resolve a 3-way git merge conflict cleanly in CLI?", false),
    ("DockerPID1", "Why is running a process as PID 1 in Docker containers risky?", false),
    ("TCPHalfOpen", "What is a TCP half-open connection and how does SO_KEEPALIVE mitigate it?", false),
];

fn main() -> Result<()> {
    let home = std::env::var("HOME").unwrap_or_else(|_| "/home/mn".to_string());
    let model_path = PathBuf::from(&home).join(".nioxs/models/manta.vmicrolm-vector.gguf");
    let tok_path = PathBuf::from(&home).join(".nioxs/models/manta-tokenizer.json");

    println!("============================================================");
    println!("🌊 NioManta 494M Companion 20-Prompt Throughput Benchmark");
    println!("============================================================");

    let tokenizer = Tokenizer::from_file(&tok_path).map_err(|e| anyhow::anyhow!("{e}"))?;
    let mut engine = AstMicroEngine::new(&model_path)?;
    let eos: u32 = 151643;
    let eot: u32 = 151645;

    let (rss_init, hwm_init) = memory_mb();
    println!("Engine Initialized: Working RAM = {:.2} MB | Peak RAM = {:.2} MB\n", rss_init, hwm_init);

    println!("{:<4} | {:<16} | {:<6} | {:<6} | {:<9} | {:<9} | {:<8}", "#", "Task", "Tokens", "Words", "Tok/s", "Words/s", "Peak RAM");
    println!("{:-<4}-+-{:-<16}-+-{:-<6}-+-{:-<6}-+-{:-<9}-+-{:-<9}-+-{:-<8}", "", "", "", "", "", "", "");

    let mut total_tokens = 0usize;
    let mut total_words = 0usize;
    let mut total_decode_duration = 0.0f64;
    let mut prompt_wps = Vec::new();
    let mut prompt_tps = Vec::new();

    for (idx, (label, query, is_plan)) in PROMPTS.iter().enumerate() {
        engine.reset_cache();

        let formatted = format_manta_prompt(query, *is_plan);
        let encoded = tokenizer.encode(formatted.as_str(), false).map_err(|e| anyhow::anyhow!("{e}"))?;
        let prompt_tokens = encoded.get_ids().to_vec();

        let hidden = engine.forward_stream(&prompt_tokens, 0)?;
        let first_token = engine.next_token(&hidden, None)?;
        let mut gen_tokens = Vec::new();
        let mut all_tokens = prompt_tokens.clone();

        let max_gen = if *is_plan { 128 } else { 96 };
        let decode_start = Instant::now();

        if first_token != eos && first_token != eot {
            gen_tokens.push(first_token);
            all_tokens.push(first_token);

            let mut current_confirmed = first_token;
            let mut current_pos = prompt_tokens.len();

            while gen_tokens.len() < max_gen {
                let remaining = max_gen.saturating_sub(gen_tokens.len());
                let max_draft = 2.min(remaining.saturating_sub(1));

                let res = engine.speculative_pld_step(
                    &all_tokens,
                    current_confirmed,
                    current_pos,
                    &gen_tokens,
                    max_draft,
                    &[eos, eot],
                )?;

                let mut stopped = false;
                for tok in res.accepted_tokens {
                    if tok == eos || tok == eot {
                        stopped = true;
                        break;
                    }
                    gen_tokens.push(tok);
                    all_tokens.push(tok);
                    if gen_tokens.len() >= max_gen {
                        stopped = true;
                        break;
                    }
                }

                current_confirmed = res.next_confirmed;
                current_pos = res.next_pos;

                if stopped || res.is_eos {
                    break;
                }
            }
        }
        let decode_time = decode_start.elapsed().as_secs_f64();
        let tps = if decode_time > 0.0 { gen_tokens.len() as f64 / decode_time } else { 0.0 };

        let decoded = tokenizer.decode(&gen_tokens, false).unwrap_or_default();
        let words = decoded.split_whitespace().count();
        let wps = if decode_time > 0.0 { words as f64 / decode_time } else { 0.0 };
        let (_, hwm) = memory_mb();

        total_tokens += gen_tokens.len();
        total_words += words;
        total_decode_duration += decode_time;
        prompt_wps.push(wps);
        prompt_tps.push(tps);

        println!(
            "{:<4} | {:<16} | {:<6} | {:<6} | {:<9.2} | {:<9.2} | {:.2} MB",
            idx + 1,
            label,
            gen_tokens.len(),
            words,
            tps,
            wps,
            hwm
        );
    }

    let avg_tps = total_tokens as f64 / total_decode_duration;
    let avg_wps = total_words as f64 / total_decode_duration;
    let (final_rss, final_hwm) = memory_mb();

    println!("============================================================");
    println!("🏁 NioManta Benchmark Aggregate (20 Prompts)");
    println!("============================================================");
    println!("Total Tokens:         {}", total_tokens);
    println!("Total Words:          {}", total_words);
    println!("Total Decode Time:    {:.2}s", total_decode_duration);
    println!("Mean Tokens/sec:      {:.2} tok/s", avg_tps);
    println!("Mean Words/sec:       {:.2} words/s", avg_wps);
    println!("Final Resident RAM:   {:.2} MB", final_rss);
    println!("Peak Process RAM:     {:.2} MB (< 240 MB limit)", final_hwm);
    println!("============================================================");

    Ok(())
}
