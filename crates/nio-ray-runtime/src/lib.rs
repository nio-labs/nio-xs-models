use anyhow::{Result, anyhow};
use candle_core::quantized::{ggml_file::qtensor_from_ggml, gguf_file, GgmlDType, QMatMul, QTensor};
use candle_core::{DType, Device, IndexOp, Module, Tensor};
use candle_transformers::quantized_nn::RmsNorm;
use memmap2::Mmap;
use std::collections::HashMap;
use std::fs::File;
use std::path::Path;

pub fn memory_mb() -> (f64, f64) {
    let status = std::fs::read_to_string("/proc/self/status").unwrap_or_default();
    let get_val = |key: &str| -> f64 {
        status
            .lines()
            .find(|l| l.starts_with(key))
            .and_then(|l| l.split_whitespace().nth(1))
            .and_then(|v| v.parse::<f64>().ok())
            .unwrap_or(0.0)
            / 1024.0
    };
    (get_val("VmRSS:"), get_val("VmHWM:"))
}

#[derive(Debug, Clone)]
pub struct Mlp {
    pub feed_forward_w1: QMatMul,
    pub feed_forward_w2: QMatMul,
    pub feed_forward_w3: QMatMul,
}

impl Mlp {
    pub fn forward(&self, xs: &Tensor) -> candle_core::Result<Tensor> {
        let w1 = self.feed_forward_w1.forward(xs)?;
        let w3 = self.feed_forward_w3.forward(xs)?;
        self.feed_forward_w2
            .forward(&(candle_nn::ops::silu(&w1)? * w3)?)
    }
}

pub struct LayerWeights {
    pub attention_wq: QMatMul,
    pub attention_wk: QMatMul,
    pub attention_wv: QMatMul,
    pub attention_bq: Tensor,
    pub attention_bk: Tensor,
    pub attention_bv: Tensor,
    pub attention_wo: QMatMul,
    pub attention_norm: RmsNorm,
    pub mlp: Mlp,
    pub ffn_norm: RmsNorm,
    pub n_head: usize,
    pub n_kv_head: usize,
    pub head_dim: usize,
    pub neg_inf: Tensor,
}

fn masked_fill(on_false: &Tensor, mask: &Tensor, on_true: &Tensor) -> candle_core::Result<Tensor> {
    let shape = mask.shape();
    let m = mask.where_cond(&on_true.broadcast_as(shape.dims())?, on_false)?;
    Ok(m)
}

fn repeat_kv(xs: Tensor, n_rep: usize) -> candle_core::Result<Tensor> {
    if n_rep == 1 {
        Ok(xs)
    } else {
        let (b_sz, n_kv_head, seq_len, head_dim) = xs.dims4()?;
        xs.unsqueeze(2)?
            .expand((b_sz, n_kv_head, n_rep, seq_len, head_dim))?
            .reshape((b_sz, n_kv_head * n_rep, seq_len, head_dim))
    }
}

impl LayerWeights {
    pub fn forward_attn(
        &self,
        x: &Tensor,
        mask: Option<&Tensor>,
        index_pos: usize,
        cos: &Tensor,
        sin: &Tensor,
        kv_cache: &mut Option<(Tensor, Tensor)>,
    ) -> candle_core::Result<Tensor> {
        let (b_sz, seq_len, n_embd) = x.dims3()?;

        let q = self.attention_wq.forward(x)?;
        let k = self.attention_wk.forward(x)?;
        let v = self.attention_wv.forward(x)?;

        let q = q.broadcast_add(&self.attention_bq)?;
        let k = k.broadcast_add(&self.attention_bk)?;
        let v = v.broadcast_add(&self.attention_bv)?;

        let q = q
            .reshape((b_sz, seq_len, self.n_head, self.head_dim))?
            .transpose(1, 2)?
            .contiguous()?;
        let k = k
            .reshape((b_sz, seq_len, self.n_kv_head, self.head_dim))?
            .transpose(1, 2)?
            .contiguous()?;
        let v = v
            .reshape((b_sz, seq_len, self.n_kv_head, self.head_dim))?
            .transpose(1, 2)?
            .contiguous()?;

        let cos_n = cos.narrow(0, index_pos, seq_len)?;
        let sin_n = sin.narrow(0, index_pos, seq_len)?;
        let q = candle_nn::rotary_emb::rope(&q.contiguous()?, &cos_n, &sin_n)?;
        let k = candle_nn::rotary_emb::rope(&k.contiguous()?, &cos_n, &sin_n)?;

        let (k, v) = match kv_cache.as_ref() {
            None => (k, v),
            Some((k_cache, v_cache)) => {
                if index_pos == 0 {
                    (k, v)
                } else {
                    let k = Tensor::cat(&[k_cache, &k], 2)?;
                    let v = Tensor::cat(&[v_cache, &v], 2)?;
                    (k, v)
                }
            }
        };
        *kv_cache = Some((k.clone(), v.clone()));

        let k = repeat_kv(k, self.n_head / self.n_kv_head)?;
        let v = repeat_kv(v, self.n_head / self.n_kv_head)?;

        let att = (q.matmul(&k.t()?)? / (self.head_dim as f64).sqrt())?;
        let att = match mask {
            None => att,
            Some(mask) => {
                let mask = mask.broadcast_as(att.shape())?;
                masked_fill(&att, &mask, &self.neg_inf)?
            }
        };
        let att = candle_nn::ops::softmax_last_dim(&att)?;
        let y = att.matmul(&v.contiguous()?)?;
        let y = y.transpose(1, 2)?.reshape(&[b_sz, seq_len, n_embd])?;
        self.attention_wo.forward(&y)
    }

    pub fn forward(
        &self,
        x: &Tensor,
        mask: Option<&Tensor>,
        index_pos: usize,
        cos: &Tensor,
        sin: &Tensor,
        kv_cache: &mut Option<(Tensor, Tensor)>,
    ) -> candle_core::Result<Tensor> {
        let residual = x;
        let x_norm = self.attention_norm.forward(x)?;
        let attn = self.forward_attn(&x_norm, mask, index_pos, cos, sin, kv_cache)?;
        let x = (attn + residual)?;

        let x_norm = self.ffn_norm.forward(&x)?;
        let mlp_out = self.mlp.forward(&x_norm)?;
        x + mlp_out
    }
}

fn precompute_freqs_cis(
    head_dim: usize,
    freq_base: f32,
    context_length: usize,
    device: &Device,
) -> candle_core::Result<(Tensor, Tensor)> {
    let theta: Vec<_> = (0..head_dim)
        .step_by(2)
        .map(|i| 1f32 / freq_base.powf(i as f32 / head_dim as f32))
        .collect();
    let theta = Tensor::new(theta.as_slice(), device)?;
    let idx_theta = Tensor::arange(0, context_length as u32, device)?
        .to_dtype(DType::F32)?
        .reshape((context_length, 1))?
        .matmul(&theta.reshape((1, theta.elem_count()))?)?;
    let cos = idx_theta.cos()?;
    let sin = idx_theta.sin()?;
    Ok((cos, sin))
}

pub struct AstMicroEngine {
    pub mmap: Mmap,
    pub content: gguf_file::Content,
    pub device: Device,
    pub block_count: usize,
    pub head_count: usize,
    pub head_count_kv: usize,
    pub head_dim: usize,
    pub embedding_length: usize,
    pub rms_norm_eps: f64,
    pub cos: Tensor,
    pub sin: Tensor,
    pub neg_inf: Tensor,
    pub output_norm: RmsNorm,
    pub output_weight: Option<QMatMul>,
    pub token_embd_offset: usize,
    pub token_embd_dtype: GgmlDType,
    pub bytes_per_token: usize,
    pub kv_caches: Vec<Option<(Tensor, Tensor)>>,
    pub masks: HashMap<usize, Tensor>,
}

impl AstMicroEngine {
    pub fn new(model_path: &Path) -> Result<Self> {
        let file = File::open(model_path)?;
        let mmap = unsafe { Mmap::map(&file)? };
        let mut cursor = std::io::Cursor::new(&mmap[..]);
        let content = gguf_file::Content::read(&mut cursor)?;
        let device = Device::Cpu;

        let md_get = |s: &str| -> Result<&gguf_file::Value> {
            content
                .metadata
                .get(s)
                .ok_or_else(|| anyhow!("missing metadata {s}"))
        };

        let head_count = md_get("qwen2.attention.head_count")?.to_u32()? as usize;
        let head_count_kv = md_get("qwen2.attention.head_count_kv")?.to_u32()? as usize;
        let embedding_length = md_get("qwen2.embedding_length")?.to_u32()? as usize;
        let context_length = md_get("qwen2.context_length")?.to_u32()? as usize;
        let block_count = md_get("qwen2.block_count")?.to_u32()? as usize;
        let rms_norm_eps = md_get("qwen2.attention.layer_norm_rms_epsilon")?.to_f32()? as f64;
        let rope_freq_base = md_get("qwen2.rope.freq_base")
            .ok()
            .and_then(|m| m.to_f32().ok())
            .unwrap_or(1000000.0);

        let head_dim = embedding_length / head_count;
        let neg_inf = Tensor::new(f32::NEG_INFINITY, &device)?;
        let (cos, sin) = precompute_freqs_cis(head_dim, rope_freq_base, context_length, &device)?;

        let norm_tensor = content.tensor(&mut cursor, "output_norm.weight", &device)?;
        let output_norm = RmsNorm::from_qtensor(norm_tensor, rms_norm_eps)?;

        let output_weight = None;

        let embd_info = content
            .tensor_infos
            .get("token_embd.weight")
            .ok_or_else(|| anyhow!("missing token_embd.weight"))?;
        let token_embd_offset = (content.tensor_data_offset + embd_info.offset) as usize;
        let token_embd_dtype = embd_info.ggml_dtype;
        let bytes_per_token = (embedding_length / token_embd_dtype.block_size()) * token_embd_dtype.type_size();

        let kv_caches = vec![None; block_count];

        Ok(Self {
            mmap,
            content,
            device,
            block_count,
            head_count,
            head_count_kv,
            head_dim,
            embedding_length,
            rms_norm_eps,
            cos,
            sin,
            neg_inf,
            output_norm,
            output_weight,
            token_embd_offset,
            token_embd_dtype,
            bytes_per_token,
            kv_caches,
            masks: HashMap::new(),
        })
    }

    pub fn reset_cache(&mut self) {
        self.kv_caches = vec![None; self.block_count];
        unsafe {
            libc::malloc_trim(0);
        }
    }

    pub fn embed(&self, tokens: &[u32]) -> Result<Tensor> {
        let seq_len = tokens.len();
        let mut raw_bytes = Vec::with_capacity(seq_len * self.bytes_per_token);
        for &tok in tokens {
            let start = self.token_embd_offset + (tok as usize) * self.bytes_per_token;
            let end = start + self.bytes_per_token;
            raw_bytes.extend_from_slice(&self.mmap[start..end]);
        }
        let qtensor = qtensor_from_ggml(
            self.token_embd_dtype,
            &raw_bytes,
            vec![1, seq_len, self.embedding_length],
            &self.device,
        )?;
        Ok(qtensor.dequantize(&self.device)?)
    }

    fn read_tensor(&self, name: &str) -> Result<QTensor> {
        let info = self
            .content
            .tensor_infos
            .get(name)
            .ok_or_else(|| anyhow!("missing tensor {name}"))?;
        let start = (self.content.tensor_data_offset + info.offset) as usize;
        let size = (info.shape.elem_count() / info.ggml_dtype.block_size()) * info.ggml_dtype.type_size();
        let slice = &self.mmap[start..start + size];
        qtensor_from_ggml(info.ggml_dtype, slice, info.shape.dims().to_vec(), &self.device)
            .map_err(|e| anyhow!("{e}"))
    }

    pub fn load_layer(&self, idx: usize) -> Result<LayerWeights> {
        let prefix = format!("blk.{idx}");
        let wq = QMatMul::from_qtensor(self.read_tensor(&format!("{prefix}.attn_q.weight"))?)?;
        let wk = QMatMul::from_qtensor(self.read_tensor(&format!("{prefix}.attn_k.weight"))?)?;
        let wv = QMatMul::from_qtensor(self.read_tensor(&format!("{prefix}.attn_v.weight"))?)?;
        let wo = QMatMul::from_qtensor(self.read_tensor(&format!("{prefix}.attn_output.weight"))?)?;

        let bq = self.read_tensor(&format!("{prefix}.attn_q.bias"))?.dequantize(&self.device)?;
        let bk = self.read_tensor(&format!("{prefix}.attn_k.bias"))?.dequantize(&self.device)?;
        let bv = self.read_tensor(&format!("{prefix}.attn_v.bias"))?.dequantize(&self.device)?;

        let attention_norm = RmsNorm::from_qtensor(
            self.read_tensor(&format!("{prefix}.attn_norm.weight"))?,
            self.rms_norm_eps,
        )?;

        let mlp = Mlp {
            feed_forward_w1: QMatMul::from_qtensor(self.read_tensor(&format!("{prefix}.ffn_gate.weight"))?)?,
            feed_forward_w2: QMatMul::from_qtensor(self.read_tensor(&format!("{prefix}.ffn_down.weight"))?)?,
            feed_forward_w3: QMatMul::from_qtensor(self.read_tensor(&format!("{prefix}.ffn_up.weight"))?)?,
        };

        let ffn_norm = RmsNorm::from_qtensor(
            self.read_tensor(&format!("{prefix}.ffn_norm.weight"))?,
            self.rms_norm_eps,
        )?;

        Ok(LayerWeights {
            attention_wq: wq,
            attention_wk: wk,
            attention_wv: wv,
            attention_bq: bq,
            attention_bk: bk,
            attention_bv: bv,
            attention_wo: wo,
            attention_norm,
            mlp,
            ffn_norm,
            n_head: self.head_count,
            n_kv_head: self.head_count_kv,
            head_dim: self.head_dim,
            neg_inf: self.neg_inf.clone(),
        })
    }

    fn mask(&mut self, t: usize) -> candle_core::Result<Tensor> {
        if let Some(mask) = self.masks.get(&t) {
            Ok(mask.clone())
        } else {
            let mask: Vec<_> = (0..t)
                .flat_map(|i| (0..t).map(move |j| u8::from(j > i)))
                .collect();
            let mask = Tensor::from_slice(&mask, (t, t), &self.device)?;
            self.masks.insert(t, mask.clone());
            Ok(mask)
        }
    }

    pub fn forward_stream(&mut self, tokens: &[u32], index_pos: usize) -> Result<Tensor> {
        let seq_len = tokens.len();
        let mask = if seq_len == 1 {
            None
        } else {
            Some(self.mask(seq_len)?)
        };

        let mut layer_in = self.embed(tokens)?;

        for layer_idx in 0..self.block_count {
            let layer = self.load_layer(layer_idx)?;
            layer_in = layer.forward(
                &layer_in,
                mask.as_ref(),
                index_pos,
                &self.cos,
                &self.sin,
                &mut self.kv_caches[layer_idx],
            )?;
        }

        unsafe {
            libc::malloc_trim(0);
        }

        let out = self.output_norm.forward(&layer_in)?;
        let last_hidden = out.i((.., seq_len - 1, ..))?;
        Ok(last_hidden)
    }

    pub fn next_token(&mut self, hidden: &Tensor, candidates: Option<&[u32]>) -> Result<u32> {
        if let Some(cands) = candidates {
            if cands.is_empty() {
                return Ok(151643); // EOS
            }
            let mut raw_bytes = Vec::with_capacity(cands.len() * self.bytes_per_token);
            for &tok in cands {
                let start = self.token_embd_offset + (tok as usize) * self.bytes_per_token;
                let end = start + self.bytes_per_token;
                raw_bytes.extend_from_slice(&self.mmap[start..end]);
            }
            let q_cand = qtensor_from_ggml(
                self.token_embd_dtype,
                &raw_bytes,
                vec![cands.len(), self.embedding_length],
                &self.device,
            )?;
            let cand_weights = q_cand.dequantize(&self.device)?;
            let logits = hidden.matmul(&cand_weights.t()?)?.squeeze(0)?;
            let logits_v: Vec<f32> = logits.to_vec1()?;
            let mut max_idx = 0;
            let mut max_val = f32::NEG_INFINITY;
            for (i, &val) in logits_v.iter().enumerate() {
                if val > max_val {
                    max_val = val;
                    max_idx = i;
                }
            }
            Ok(cands[max_idx])
        } else {
            if self.output_weight.is_none() {
                let mut cursor = std::io::Cursor::new(&self.mmap[..]);
                let w = match self.content.tensor(&mut cursor, "output.weight", &self.device) {
                    Ok(v) => QMatMul::from_qtensor(v)?,
                    _ => QMatMul::from_qtensor(self.content.tensor(&mut cursor, "token_embd.weight", &self.device)?)?,
                };
                self.output_weight = Some(w);
            }
            let logits = self.output_weight.as_ref().unwrap().forward(hidden)?.squeeze(0)?;
            let logits_v: Vec<f32> = logits.to_vec1()?;
            let mut max_idx = 0;
            let mut max_val = f32::NEG_INFINITY;
            for (i, &val) in logits_v.iter().enumerate() {
                if val > max_val {
                    max_val = val;
                    max_idx = i;
                }
            }
            Ok(max_idx as u32)
        }
    }
}
