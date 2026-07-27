#!/usr/bin/env python3
"""LoRA training for Qwen2.5-7B on RTX 2060 SUPER (8GB).

Ultra memory-efficient:
- QLoRA 4-bit with double quant
- Gradient checkpointing
- Sequence length 512
- LoRA r=8, alpha=16, q+v only
- Batch size 1, grad accum 32
- CPU offload for optimizer states

Usage:
  python3 scripts/train_lora_7b.py
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
    output_dir = "/mnt/data/openmythos/models/open-djicht-lora-7b"

    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    print(f"Model: {model_name}")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

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

    # Minimal LoRA for 7B on 8GB
    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.0,
        target_modules=["q_proj", "v_proj"],
        task_type=TaskType.CAUSAL_LM,
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Dataset
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
    print(f"Samples: {len(dataset)}")

    # Training args — maximum memory efficiency
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=3,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=32,
        learning_rate=1e-4,
        warmup_steps=10,
        lr_scheduler_type="cosine",
        logging_steps=5,
        save_strategy="epoch",
        fp16=True,
        optim="paged_adamw_8bit",
        report_to="none",
        max_grad_norm=0.3,
        dataloader_num_workers=0,
        remove_unused_columns=False,
        gradient_checkpointing=True,
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )

    print("Starting training...")
    trainer.train()

    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Saved to {output_dir}")

    peak = torch.cuda.max_memory_allocated() / 1e9
    print(f"Peak VRAM: {peak:.1f} GB")


if __name__ == "__main__":
    main()
