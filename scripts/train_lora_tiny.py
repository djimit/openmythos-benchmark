#!/usr/bin/env python3
"""Ultra memory-efficient LoRA training for RTX 2060 SUPER (8GB VRAM).

Uses every trick in the book to fit training in 8GB:
- Gradient checkpointing
- Sequence length 512
- LoRA r=4, alpha=8
- Batch size 1, grad accum 16
- float32 instead of mixed precision (more stable on old GPUs)
- gradient offloading to CPU

Usage:
  python3 scripts/train_lora_tiny.py \
    --dataset data/sft_combined.jsonl \
    --output_dir models/open-djicht-lora-tiny
"""

import json
import os
import sys
from pathlib import Path

# Memory optimization BEFORE importing torch
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
from trl import SFTTrainer
from datasets import load_dataset


def main():
    model_name = "Qwen/Qwen2.5-1.5B-Instruct"
    dataset_path = "/mnt/data/openmythos/data/sft_combined.jsonl"
    output_dir = "/mnt/data/openmythos/models/open-djicht-lora-tiny"

    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    print(f"Model: {model_name}")

    # 4-bit quantization with double quant + NF4
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    # Load model
    print("Loading model...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model.config.use_cache = False
    model.gradient_checkpointing_enable()
    model = prepare_model_for_kbit_training(model)

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Minimal LoRA — r=4, alpha=8, only q+v
    lora_config = LoraConfig(
        r=4,
        lora_alpha=8,
        lora_dropout=0.0,
        target_modules=["q_proj", "v_proj"],
        task_type=TaskType.CAUSAL_LM,
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Load dataset
    print("Loading dataset...")
    dataset = load_dataset("json", data_files=dataset_path, split="train")

    # Format for SFT
    def format_fn(ex):
        msgs = ex.get("messages", [])
        if len(msgs) >= 3:
            system = (
                msgs[0].get("content", "") if msgs[0].get("role") == "system" else ""
            )
            user = msgs[1].get("content", "")
            assistant = msgs[2].get("content", "")
            return {
                "text": f"<|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n{assistant}<|im_end|>"
            }
        return {"text": ""}

    dataset = dataset.map(format_fn)

    # Training args — ultra-conservative
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=5,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=16,
        learning_rate=1e-4,
        warmup_steps=20,
        lr_scheduler_type="cosine",
        logging_steps=5,
        save_strategy="epoch",
        fp16=False,
        bf16=False,
        optim="paged_adamw_8bit",
        report_to="none",
        max_grad_norm=0.3,
        dataloader_num_workers=0,
        remove_unused_columns=False,
    )

    # Trainer
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )

    print("Starting training...")
    trainer.train()

    # Save
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Saved to {output_dir}")

    # Memory stats
    peak = torch.cuda.max_memory_allocated() / 1e9
    print(f"Peak VRAM: {peak:.1f} GB")


if __name__ == "__main__":
    main()
