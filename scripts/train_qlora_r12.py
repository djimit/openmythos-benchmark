#!/usr/bin/env python3
"""QLoRA fine-tuning for OpenMythos R12 governance model.

Trains qwen2.5-coder:7b with 4-bit QLoRA on governance SFT data.
Requires: torch, transformers, peft, trl, datasets, accelerate, bitsandbytes

This script is ready to run. Install deps first:
    pip install torch transformers peft trl datasets accelerate bitsandbytes

Usage:
    python3 scripts/train_qlora_r12.py
    python3 scripts/train_qlora_r12.py --epochs 5 --lr 2e-4
"""

import argparse
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
OUTPUT_DIR = REPO_ROOT / "models" / "openmythos-r12-qlora"


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def check_deps():
    """Check required packages."""
    missing = []
    for pkg in [
        "torch",
        "transformers",
        "peft",
        "trl",
        "datasets",
        "accelerate",
        "bitsandbytes",
    ]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"Missing: {', '.join(missing)}")
        print(f"Run: pip install {' '.join(missing)}")
        return False
    import torch

    if torch.cuda.is_available():
        print(
            f"GPU: {torch.cuda.get_device_name(0)} ({torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB)"
        )
    else:
        print("WARNING: No GPU — training will be slow")
    return True


def train(
    base_model: str = "Qwen/Qwen2.5-Coder-7B-Instruct",
    epochs: int = 3,
    lr: float = 2e-4,
    batch_size: int = 4,
    grad_accum: int = 4,
):
    """Run QLoRA fine-tuning."""
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
        DataCollatorForLanguageModeling,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer
    from datasets import Dataset
    import torch

    # Load data
    data = load_jsonl(DATASET_PATH)
    print(f"Loaded {len(data)} training examples")

    # Format for SFT
    def format_example(ex):
        return f"### Instruction:\n{ex['instruction']}\n\n### Response:\n{ex['output']}"

    texts = [format_example(ex) for ex in data]
    dataset = Dataset.from_dict({"text": texts})

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token

    # 4-bit quantization
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    # Load model
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model = prepare_model_for_kbit_training(model)

    # LoRA config
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Training args
    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum,
        learning_rate=lr,
        warmup_ratio=0.1,
        logging_steps=10,
        save_strategy="epoch",
        optim="paged_adamw_8bit",
        fp16=torch.cuda.is_available(),
        report_to="none",
    )

    # Trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=training_args,
        formatting_func=lambda x: x["text"],
        max_seq_length=2048,
    )

    # Train
    print(f"Starting training: {epochs} epochs, lr={lr}, batch={batch_size}")
    trainer.train()

    # Save
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))
    print(f"Model saved to {OUTPUT_DIR}")

    return OUTPUT_DIR


def demo():
    """Self-check without training."""
    data = load_jsonl(DATASET_PATH)
    print(f"R12 QLoRA Training Config:")
    print(f"  Base model: Qwen/Qwen2.5-Coder-7B-Instruct")
    print(f"  Dataset: {len(data)} examples from {DATASET_PATH.name}")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"  Estimated VRAM: ~6GB (4-bit)")
    print(f"  Estimated time: ~2-4 hours on RTX 2060 / ~30min on M-series")
    print()
    print("To start training:")
    print("  pip install torch transformers peft trl datasets accelerate bitsandbytes")
    print("  python3 scripts/train_qlora_r12.py")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo:
        return demo()

    if not check_deps():
        return 1

    train(epochs=args.epochs, lr=args.lr, batch_size=args.batch_size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
