#!/usr/bin/env python3
"""LoRA fine-tuning pipeline for OpenDjicht on workstation (RTX 2060 SUPER).

Trains Qwen2.5-14B with LoRA on governance SFT data.
Requires: torch, transformers, peft, trl, datasets, accelerate, bitsandbytes

Usage:
  python3 scripts/train_lora.py \
    --dataset analysis/openmythos-apex-runs/datasets/frontier-distill/sft_combined.jsonl \
    --output_dir models/open-djicht-lora-v1

Prerequisites (run on workstation):
  pip install torch transformers peft trl datasets accelerate bitsandbytes
"""

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows


def check_dependencies():
    """Check if required packages are installed."""
    missing = []
    for pkg in ["torch", "transformers", "peft", "trl", "datasets", "accelerate"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"Missing packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)} bitsandbytes")
        return False

    # Check CUDA
    import torch

    if not torch.cuda.is_available():
        print("WARNING: CUDA not available. Training will be very slow on CPU.")
    else:
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    return True


def prepare_dataset(dataset_path: Path, output_dir: Path):
    """Convert SFT JSONL to HuggingFace datasets format."""
    rows = load_jsonl(dataset_path)

    # Convert to instruction format
    data = []
    skipped = 0
    for row in rows:
        msgs = row.get("messages", [])
        by_role = {m.get("role"): m.get("content", "") for m in msgs}
        user = by_role.get("user", "")
        assistant = by_role.get("assistant", "")
        system = by_role.get("system", "")

        if user and assistant:
            text = f"<|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n{assistant}<|im_end|>"
            category = row.get("category") or row.get("metadata", {}).get("category", "")
            data.append({"text": text, "category": category})
        else:
            skipped += 1

    if skipped:
        print(f"WARNING: skipped {skipped} row(s) missing a user/assistant message")

    # Save as JSONL for datasets library
    output_path = output_dir / "train.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        for d in data:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    print(f"Prepared {len(data)} training samples → {output_path}")
    return output_path


def train(args):
    """Run LoRA training."""
    import torch
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        TrainingArguments,
        BitsAndBytesConfig,
    )
    from peft import LoraConfig, get_peft_model, TaskType
    from trl import SFTTrainer
    from datasets import load_dataset

    # Load model in 4-bit
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    print(f"Loading model: {args.base_model}")
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16,
    )
    model.config.use_cache = False

    tokenizer = AutoTokenizer.from_pretrained(
        args.base_model,
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # LoRA config
    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=[
            "q_proj",
            "v_proj",
            "k_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        task_type=TaskType.CAUSAL_LM,
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Load dataset — format for TRL >= 1.9
    raw_dataset = load_dataset("json", data_files=str(args.dataset), split="train")
    # Ensure 'text' column exists for SFTTrainer
    if "text" not in raw_dataset.column_names:

        def format_example(ex):
            msgs = ex.get("messages", [])
            if len(msgs) >= 3:
                system = (
                    msgs[0].get("content", "")
                    if msgs[0].get("role") == "system"
                    else ""
                )
                user = msgs[1].get("content", "")
                assistant = msgs[2].get("content", "")
                return {
                    "text": f"<|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n{assistant}<|im_end|>"
                }
            return {"text": ""}

        raw_dataset = raw_dataset.map(format_example)
    dataset = raw_dataset

    # Training arguments
    training_args = TrainingArguments(
        output_dir=str(args.output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        warmup_steps=50,
        lr_scheduler_type="cosine",
        logging_steps=10,
        save_strategy="epoch",
        bf16=False,
        fp16=False,
        optim="paged_adamw_8bit",
        report_to="none",
    )

    # Trainer (TRL >= 1.9 API)
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )

    print("Starting training...")
    trainer.train()

    # Save
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"Model saved to {args.output_dir}")


def main():
    parser = argparse.ArgumentParser(description="LoRA training for OpenDjicht")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument(
        "--output_dir", type=Path, default=REPO_ROOT / "models" / "open-djicht-lora-v1"
    )
    parser.add_argument("--base_model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--gradient_accumulation_steps", type=int, default=2)
    parser.add_argument("--learning_rate", type=float, default=2e-4)
    parser.add_argument("--lora_r", type=int, default=16)
    parser.add_argument("--lora_alpha", type=int, default=32)
    parser.add_argument("--lora_dropout", type=float, default=0.05)
    parser.add_argument("--max_seq_length", type=int, default=2048)
    parser.add_argument(
        "--check_only", action="store_true", help="Only check dependencies"
    )
    args = parser.parse_args()

    if not check_dependencies():
        sys.exit(1)

    if args.check_only:
        print("Dependencies OK")
        return 0

    train(args)


if __name__ == "__main__":
    sys.exit(main())
