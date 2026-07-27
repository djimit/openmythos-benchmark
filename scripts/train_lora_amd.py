#!/usr/bin/env python3
"""LoRA training for OpenDjicht on AMD Radeon R9700 (ROCm).

Uses the full 34GB VRAM available for larger models.
Trains Qwen2.5-7B with QLoRA for governance tasks.

Usage:
  python3 scripts/train_lora_amd.py \
    --dataset data/sft_combined.jsonl \
    --output_dir models/open-djicht-lora-amd-v1
"""

import json
import os
import sys
from pathlib import Path

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
    model_name = "Qwen/Qwen2.5-7B-Instruct"
    dataset_path = "/mnt/data/openmythos/data/sft_combined.jsonl"
    output_dir = "/mnt/data/openmythos/models/open-djicht-lora-amd-v1"

    print(f"PyTorch: {torch.__version__}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    print(f"Model: {model_name}")

    # 4-bit quantization
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # Load model
    print("Loading model in 4-bit...")
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

    # LoRA — r=16 for 7B model
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
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

    # Load dataset
    print("Loading dataset...")
    dataset = load_dataset("json", data_files=dataset_path, split="train")

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
    print(f"Training samples: {len(dataset)}")

    # Training args
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=5,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        warmup_steps=20,
        lr_scheduler_type="cosine",
        logging_steps=5,
        save_strategy="epoch",
        bf16=True,
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

    peak = torch.cuda.max_memory_allocated() / 1e9
    print(f"Peak VRAM: {peak:.1f} GB")


if __name__ == "__main__":
    main()
