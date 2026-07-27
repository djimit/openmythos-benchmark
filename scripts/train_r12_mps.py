#!/usr/bin/env python3
"""R12 LoRA fine-tuning for Apple Silicon (MPS).

Uses Qwen2.5-Coder-3B (fits in RAM with fp16 + LoRA).
Falls back to CPU if MPS fails.

Usage:
    source .venv/bin/activate
    python3 scripts/train_r12_mps.py
"""

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DATASET_PATH = (
    REPO_ROOT
    / "analysis"
    / "openmythos-apex-runs"
    / "datasets"
    / "apex-r10-sft-gemma4.jsonl"
)
OUTPUT_DIR = REPO_ROOT / "models" / "openmythos-r12-lora-3b"


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main():
    import torch
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        TrainingArguments,
        DataCollatorForLanguageModeling,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer
    from datasets import Dataset

    # Device selection
    if torch.backends.mps.is_available():
        device = "mps"
        dtype = torch.float16
        print("Using MPS (Apple GPU)")
    else:
        device = "cpu"
        dtype = torch.float32
        print("Using CPU")

    # Load data
    data = load_jsonl(DATASET_PATH)
    print(f"Loaded {len(data)} training examples")

    def format_example(ex):
        return f"### Instruction:\n{ex['instruction']}\n\n### Response:\n{ex['output']}"

    texts = [format_example(ex) for ex in data]
    dataset = Dataset.from_dict({"text": texts})

    # Model — 3B fits in RAM on Apple Silicon
    base_model = "Qwen/Qwen2.5-Coder-3B-Instruct"
    print(f"Loading {base_model}...")

    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=dtype,
        device_map="auto" if device == "mps" else {"": device},
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )

    # LoRA config
    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Training args
    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        num_train_epochs=5,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,
        warmup_ratio=0.1,
        logging_steps=5,
        save_strategy="epoch",
        fp16=(device == "mps"),
        optim="adamw_torch",
        report_to="none",
        dataloader_num_workers=0,  # MPS requires 0
    )

    # Trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=training_args,
        formatting_func=lambda x: x["text"],
        max_seq_length=1024,
    )

    print(f"Starting training: 5 epochs, batch=2, grad_accum=8")
    print(f"Estimated time: ~30-60 min on MPS")

    trainer.train()

    # Save
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))

    # Save metadata
    meta = {
        "base_model": base_model,
        "training_data": str(DATASET_PATH),
        "examples": len(data),
        "epochs": 5,
        "lora_r": 8,
        "device": device,
    }
    (OUTPUT_DIR / "training_meta.json").write_text(json.dumps(meta, indent=2))

    print(f"\nModel saved to {OUTPUT_DIR}")
    print(f"To merge and export: python3 scripts/merge_lora.py --model {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    import psutil

    ram_gb = psutil.virtual_memory().total / 1e9
    free_gb = psutil.virtual_memory().available / 1e9
    print(f"RAM: {ram_gb:.1f} GB total, {free_gb:.1f} GB free")
    if free_gb < 6:
        print("WARNING: < 6GB free RAM. Training may OOM.")
        print("Close other applications first.")
    sys.exit(main())
