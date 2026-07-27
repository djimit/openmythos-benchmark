#!/usr/bin/env python3
"""R16 7B QLoRA fine-tuning for OpenMythos governance model.

Trains qwen2.5-coder:7b with QLoRA 4-bit on governance SFT data.
Requires: torch, transformers, peft, trl, datasets, accelerate, bitsandbytes

Usage (on workstation):
    source .venv/bin/activate
    python3 scripts/train_r16_7b.py
"""

import json, sys, os
from pathlib import Path

# Config
BASE_MODEL = "Qwen/Qwen2.5-Coder-7B-Instruct"
DATASET = Path("/home/djimit/openmythos/datasets/r15-merged-sft.jsonl")
OUTPUT = Path("/home/djimit/openmythos/models/r16-qlora-7b")
LORA_R = 32
LORA_ALPHA = 64
EPOCHS = 5
BATCH_SIZE = 2
GRAD_ACCUM = 8
LR = 2e-4


def main():
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer
    from datasets import Dataset
    import torch

    # Load data
    data = [json.loads(l) for l in DATASET.open() if l.strip()]
    print(f"Loaded {len(data)} training examples")

    def fmt(ex):
        return f"### Instruction:\n{ex['instruction']}\n\n### Response:\n{ex['output']}"

    dataset = Dataset.from_dict({"text": [fmt(ex) for ex in data]})

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token

    # 4-bit quantization
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    print(f"Loading {BASE_MODEL} (4-bit, CPU only)...")
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb,
        device_map={"": "cpu"},
        trust_remote_code=True,
    )
    model = prepare_model_for_kbit_training(model)

    # LoRA
    lora = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
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
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    # Training args
    args = TrainingArguments(
        output_dir=str(OUTPUT),
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=16,
        learning_rate=LR,
        warmup_steps=10,
        logging_steps=10,
        save_strategy="epoch",
        optim="adamw_torch",
        fp16=False,
        bf16=False,
        dataloader_num_workers=4,
        max_grad_norm=1.0,
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=dataset,
        args=args,
        formatting_func=lambda x: x["text"],
    )

    print(f"Starting R16: {EPOCHS} epochs, QLoRA 4-bit 7B, batch={BATCH_SIZE}")
    trainer.train()

    trainer.save_model(str(OUTPUT))
    tokenizer.save_pretrained(str(OUTPUT))

    meta = {
        "run": "R16",
        "base_model": BASE_MODEL,
        "examples": len(data),
        "epochs": EPOCHS,
        "lora_r": LORA_R,
        "lora_alpha": LORA_ALPHA,
        "quantization": "4-bit",
        "batch_size": BATCH_SIZE,
        "grad_accum": GRAD_ACCUM,
        "learning_rate": LR,
        "device": "RTX 2060 SUPER 8GB",
    }
    (OUTPUT / "training_meta.json").write_text(json.dumps(meta, indent=2))
    print(f"Saved to {OUTPUT}")


if __name__ == "__main__":
    os.environ["CUDA_VISIBLE_DEVICES"] = ""  # Force CPU only
    main()
