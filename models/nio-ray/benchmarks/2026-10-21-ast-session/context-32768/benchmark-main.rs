use anyhow::{Result,anyhow,ensure};
use nio_ray_runtime::{AstMicroEngine,memory_mb};
use serde_json::{json,Value};
use std::{io::{self,Write},path::Path,time::Instant};
use tokenizers::Tokenizer;
fn main()->Result<()> {
 let a:Vec<String>=std::env::args().collect();
 ensure!(a.len()==6,"usage: MODEL TOKENIZER ray|viper PROMPTS_JSON MAX_NEW_TOKENS");
 let cap:usize=a[5].parse()?;ensure!(cap>0,"generation cap must be positive");
 let prompts:Vec<Value>=serde_json::from_str(&std::fs::read_to_string(&a[4])?)?;
 ensure!(prompts.len()==20,"expected 20 prompts");
 let started=Instant::now();
 let tok=Tokenizer::from_file(&a[2]).map_err(|e|anyhow!("{e}"))?;
 let mut engine=AstMicroEngine::new(Path::new(&a[1]))?;
 let initial=memory_mb();
 let eos=tok.token_to_id("<|im_end|>").ok_or_else(||anyhow!("missing EOS"))?;
 let eot=tok.token_to_id("<|endoftext|>").ok_or_else(||anyhow!("missing EOT"))?;
 let pool=if a[3]=="viper" {nio_viper_runtime::tactical_candidates(&tok)?}else{
  let sample="fn main() { println!(\"Hello, world!\"); let mut x = 42; return Ok(()); } \n  \"'";
  let mut ids=tok.encode(sample,false).map_err(|e|anyhow!("{e}"))?.get_ids().to_vec();
  ids.push(eos);ids.push(eot);ids.sort_unstable();ids.dedup();ids
 };
 let mut out=io::BufWriter::new(io::stdout().lock());
 writeln!(out,"{}",json!({"type":"load","model":a[3],"layers":engine.block_count,"vocab":engine.vocab_size,"candidates":pool.len(),"rss_mib":initial.0,"hwm_mib":initial.1,"load_ms":started.elapsed().as_secs_f64()*1000.,"threads":std::env::var("RAYON_NUM_THREADS").ok(),"max_new_tokens":cap,"reset":"KV cache reset between independent tasks; same process, engine, tokenizer, mmap, masks and candidate pool retained"}))?;out.flush()?;
 for p in prompts {
  engine.reset_cache();
  let text=p["prompt"].as_str().ok_or_else(||anyhow!("invalid prompt"))?;
  let formatted=format!("<|im_start|>user\n{text}<|im_end|>\n<|im_start|>assistant\n");
  let ids=tok.encode(formatted.as_str(),false).map_err(|e|anyhow!("{e}"))?.get_ids().to_vec();
  let pre=memory_mb();
  let t=Instant::now();let h=engine.forward_stream(&ids,0)?;let prefill_ms=t.elapsed().as_secs_f64()*1000.;
  let post_pref=memory_mb();
  let mut next=engine.next_token(&h,Some(&pool))?;
  let first=next;let mut generated=Vec::new();let mut decode_steps=0;
  let decode=Instant::now();let mut reason="length";
  for step in 0..cap {
   if next==eos||next==eot {reason="eos";break;}
   generated.push(next);
   if step+1<cap {
    let sh=engine.forward_stream(&[next],ids.len()+step)?;
    next=engine.next_token(&sh,Some(&pool))?;decode_steps+=1;
   }
  }
  let decode_ms=decode.elapsed().as_secs_f64()*1000.;
  let decoded=tok.decode(&generated,false).map_err(|e|anyhow!("{e}"))?;
  let end=memory_mb();
  writeln!(out,"{}",json!({"type":"prompt","model":a[3],"id":p["id"],"title":p["title"],"prompt":text,"prompt_tokens":ids.len(),"generated_tokens":generated.len(),"first_token":first,"stop_reason":reason,"generated_ids":generated,"output":decoded,"prefill_ms":prefill_ms,"decode_steps":decode_steps,"decode_ms":decode_ms,"decode_tps":if decode_steps>0{Some(decode_steps as f64*1000./decode_ms)}else{None},"rss_before_mib":pre.0,"rss_after_prefill_mib":post_pref.0,"rss_after_prompt_mib":end.0,"process_hwm_after_prefill_mib":post_pref.1,"process_hwm_mib":end.1}))?;out.flush()?;
 }
 let mem=memory_mb();
 writeln!(out,"{}",json!({"type":"end","model":a[3],"prompts":20,"rss_mib":mem.0,"peak_rss_mib":mem.1,"wall_seconds":started.elapsed().as_secs_f64()}))?;out.flush()?;
 Ok(())
}
