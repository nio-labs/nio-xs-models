#!/usr/bin/env python3
"""
⚡ NIOCUDA (~310M) TACTICAL SWARM CONDUCTOR TRAINING & GGUF QUANTIZATION PIPELINE
- Base Model: Qwen/Qwen2.5-Coder-0.5B-Instruct
- Depth Slicing: 24 Layers -> 16 Transformer Layers (~310M Parameters)
- Hidden Dimension: d = 896 (896 / 32 = 28 blocks -> 100% 32-byte SIMD clean Q4_0 alignment)
- Target Output: Structured XML Swarm Execution Plans (<cuda_plan> and <cuda_dag>)
- Quantization Target: nio-cuda-ast.Q4_0.gguf (~146 MB on disk, < 160 MB resident RAM)
- Target Hardware: Google Colab T4 / L4 / A100 GPU (< 15 mins total)
"""

import os
import sys
import time
import json
import shutil
import subprocess
from pathlib import Path

# Force unbuffered output and optimize CUDA memory allocation
os.environ["PYTHONUNBUFFERED"] = "1"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

# Remove torchao if present to avoid PEFT conflict
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "torchao"], capture_output=True)

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForCausalLM, get_cosine_schedule_with_warmup
from peft import LoraConfig, get_peft_model

print("=" * 80, flush=True)
print("⚡ NIOCUDA (~310M) TACTICAL SWARM CONDUCTOR TRAINING & EXPORT PIPELINE", flush=True)
print("=" * 80, flush=True)

# ------------------------------------------------------------------------------
# 1. Hardware Verification
# ------------------------------------------------------------------------------
if not torch.cuda.is_available():
    print("❌ ERROR: CUDA GPU not detected! Colab runtime must have GPU enabled.", flush=True)
    sys.exit(1)

device_name = torch.cuda.get_device_name(0)
total_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
print(f"✅ GPU Detected: {device_name} ({total_vram_gb:.2f} GB VRAM)", flush=True)

# ------------------------------------------------------------------------------
# 2. Check / Build llama.cpp (for GGUF conversion & Q4_0 quant)
# ------------------------------------------------------------------------------
llama_quant_bin = Path("/content/llama.cpp/build/bin/llama-quantize")

llama_build_proc = None
if llama_quant_bin.exists():
    print("✅ llama-quantize already compiled and ready!", flush=True)
else:
    print("\n🛠 [1/6] Launching llama.cpp background build for GGUF quantization...", flush=True)
    build_cmd = """
    set -e
    if [ ! -d "/content/llama.cpp" ]; then
        git clone --depth 1 https://github.com/ggml-org/llama.cpp /content/llama.cpp
    fi
    cd /content/llama.cpp
    pip install -q gguf
    cmake -B build -DGGML_CUDA=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_SERVER=OFF -DLLAMA_CURL=OFF
    cmake --build build --target llama-quantize -j$(nproc)
    """
    llama_build_proc = subprocess.Popen(
        ["bash", "-c", build_cmd],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    print("   llama.cpp build running asynchronously.", flush=True)

# ------------------------------------------------------------------------------
# 3. Load & Slice Qwen2.5-Coder-0.5B to 16 Layers (~310M Params)
# ------------------------------------------------------------------------------
BASE_MODEL = "Qwen/Qwen2.5-Coder-0.5B-Instruct"
TARGET_LAYERS = 16

print(f"\n📥 [2/6] Loading base model {BASE_MODEL} and slicing to {TARGET_LAYERS} layers...", flush=True)
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Load model directly to cuda without device_map="auto" to allow clean layer slicing
raw_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.float16,
    trust_remote_code=True
).to("cuda")

original_layers = len(raw_model.model.layers)
print(f"   Original layers: {original_layers} | Vocab size: {raw_model.config.vocab_size}", flush=True)

# Slicing: keep first 16 layers
raw_model.model.layers = nn.ModuleList(raw_model.model.layers[:TARGET_LAYERS])
raw_model.config.num_hidden_layers = TARGET_LAYERS
if hasattr(raw_model.config, 'layer_types') and raw_model.config.layer_types is not None:
    raw_model.config.layer_types = raw_model.config.layer_types[:TARGET_LAYERS]

for idx, layer in enumerate(raw_model.model.layers):
    layer.self_attn.layer_idx = idx

total_params = sum(p.numel() for p in raw_model.parameters())
print(f"✅ Sliced to {TARGET_LAYERS} layers. Active Parameters: {total_params / 1e6:.2f}M", flush=True)

# ------------------------------------------------------------------------------
# 4. Attach LoRA Adapters for Conductor Coordination Plans
# ------------------------------------------------------------------------------
print("\n🧬 [3/6] Attaching LoRA adapters for tactical DAG & plan coordination...", flush=True)
peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
# Enable gradient checkpointing to keep VRAM < 4 GB on Tesla T4
raw_model.gradient_checkpointing_enable()

model = get_peft_model(raw_model, peft_config)
model.print_trainable_parameters()

# ------------------------------------------------------------------------------
# 5. Dataset Loading & Training
# ------------------------------------------------------------------------------
print("\n📚 [4/6] Loading NioCuda conductor dataset...", flush=True)
DATASET_FILE = Path("/content/nio_cuda_conductor_data.jsonl")
if not DATASET_FILE.exists():
    DATASET_FILE = Path("scripts/nio_cuda_conductor_data.jsonl")

train_texts = []
if DATASET_FILE.exists():
    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            msgs = item.get("messages", [])
            rendered = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
            train_texts.append(rendered)
    print(f"   Loaded {len(train_texts):,} tactical conductor samples.", flush=True)
else:
    print(f"❌ ERROR: Dataset file not found at {DATASET_FILE}", flush=True)
    sys.exit(1)

class CudaDataset(Dataset):
    def __init__(self, texts, tok, max_len=384):
        self.encodings = tok(
            texts,
            truncation=True,
            max_length=max_len,
            padding="max_length",
            return_tensors="pt"
        )
        self.pad_token_id = tok.pad_token_id
        
    def __len__(self):
        return len(self.encodings["input_ids"])
        
    def __getitem__(self, idx):
        input_ids = self.encodings["input_ids"][idx]
        attention_mask = self.encodings["attention_mask"][idx]
        labels = input_ids.clone()
        labels[labels == self.pad_token_id] = -100
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels
        }

dataset = CudaDataset(train_texts, tokenizer, max_len=384)
batch_size = 2
grad_accum_steps = 4
loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
optimizer = torch.optim.AdamW(model.parameters(), lr=2e-4, weight_decay=0.01)

epochs = 2
total_update_steps = (len(loader) // grad_accum_steps) * epochs
scheduler = get_cosine_schedule_with_warmup(
    optimizer,
    num_warmup_steps=int(total_update_steps * 0.05),
    num_training_steps=total_update_steps
)

print(f"\n🚀 [5/6] Training NioCuda for {epochs} epochs ({total_update_steps} optimization steps, effective batch size={batch_size * grad_accum_steps})...", flush=True)
model.train()
opt_step = 0
start_time = time.time()

for epoch in range(epochs):
    epoch_loss = 0.0
    optimizer.zero_grad()
    for batch_idx, batch in enumerate(loader):
        input_ids = batch["input_ids"].to("cuda")
        attention_mask = batch["attention_mask"].to("cuda")
        labels = batch["labels"].to("cuda")

        outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
        loss = outputs.loss / grad_accum_steps
        loss.backward()
        epoch_loss += outputs.loss.item()

        if (batch_idx + 1) % grad_accum_steps == 0 or (batch_idx + 1) == len(loader):
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
            opt_step += 1

            if opt_step % 25 == 0 or opt_step == total_update_steps:
                print(f"   [Epoch {epoch+1}/{epochs} | Step {opt_step}/{total_update_steps}] Loss: {outputs.loss.item():.4f} | LR: {scheduler.get_last_lr()[0]:.2e}", flush=True)

    avg_loss = epoch_loss / len(loader)
    print(f"✅ Epoch {epoch+1}/{epochs} Complete. Average Loss: {avg_loss:.4f}", flush=True)

train_duration = time.time() - start_time
print(f"🎉 Training finished in {train_duration/60:.2f} minutes.", flush=True)

# ------------------------------------------------------------------------------
# 6. Merge LoRA & Export to PyTorch / GGUF
# ------------------------------------------------------------------------------
print("\n💾 [6/6] Merging LoRA adapters and exporting to PyTorch & GGUF...", flush=True)
merged_model = model.merge_and_unload()
export_dir = Path("/content/nio-cuda-merged")
export_dir.mkdir(parents=True, exist_ok=True)
merged_model.save_pretrained(export_dir)
tokenizer.save_pretrained(export_dir)
print(f"✅ Exported merged PyTorch model to {export_dir}", flush=True)

# Copy standalone tokenizer.json
tok_src = export_dir / "tokenizer.json"
tok_dst = Path("/content/nio-cuda-tokenizer.json")
if tok_src.exists():
    shutil.copyfile(tok_src, tok_dst)
    print(f"✅ Standalone tokenizer saved to {tok_dst}", flush=True)

# Wait for llama.cpp build to finish if it was launched
if llama_build_proc:
    print("   Waiting for llama.cpp background build...", flush=True)
    llama_build_proc.wait()

# Convert to FP16 GGUF
print("\n⚙️  Converting PyTorch model to FP16 GGUF...", flush=True)
gguf_f16_path = Path("/content/nio-cuda-f16.gguf")
subprocess.run([
    sys.executable, "/content/llama.cpp/convert_hf_to_gguf.py",
    str(export_dir),
    "--outfile", str(gguf_f16_path),
    "--outtype", "f16"
], check=True)

# Quantize to clean Q4_0 (32-byte block-aligned)
gguf_q4_path = Path("/content/nio-cuda-ast.Q4_0.gguf")
print(f"\n📦 Quantizing to 32-byte block-aligned Q4_0 -> {gguf_q4_path}...", flush=True)
subprocess.run([
    str(llama_quant_bin),
    str(gguf_f16_path),
    str(gguf_q4_path),
    "Q4_0"
], check=True)

if gguf_q4_path.exists():
    sz_mb = gguf_q4_path.stat().st_size / (1024**2)
    print("=" * 80, flush=True)
    print(f"🎉 SUCCESS! NioCuda Conductor compiled: {gguf_q4_path} ({sz_mb:.2f} MiB)", flush=True)
    print(f"   Target resident RAM: < 160 MB on CPU / Native Candle", flush=True)
    print("=" * 80, flush=True)
