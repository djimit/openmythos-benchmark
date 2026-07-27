#!/usr/bin/env python3
"""
R16 7B QLoRA Training — Copy-paste into Google Colab cell

INSTRUCTIONS:
1. Open https://colab.research.google.com
2. Runtime → Change runtime type → GPU (T4)
3. Paste this entire script into a code cell
4. Run (will take 2-3 hours)
5. Download the output GGUF

DATA UPLOAD:
- Upload r15-merged-sft.jsonl to Colab (left panel → Files → Upload)
- Or run: from google.colab import files; uploaded = files.upload()
"""

# === Cell 1: Install ===
# !pip install -q unsloth transformers datasets trl accelerate bitsandbytes

# === Cell 2: Load model ===
from unsloth import FastLanguageModel
import torch

MODEL = "unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit"
MAX_LEN = 2048

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL,
    max_seq_length=MAX_LEN,
    dtype=None,
    load_in_4bit=True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=32,
    lora_alpha=64,
    lora_dropout=0.05,
    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ],
    bias="none",
)

# === Cell 3: Load data ===
from datasets import load_dataset

dataset = load_dataset(
    "json", data_files="/content/r15-merged-sft.jsonl", split="train"
)
dataset = dataset.map(
    lambda x: {
        "text": f"### Instruction:\n{x['instruction']}\n\n### Response:\n{x['output']}"
    }
)
print(f"Dataset: {len(dataset)} examples")

# === Cell 4: Train ===
from trl import SFTTrainer
from transformers import TrainingArguments

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=MAX_LEN,
    args=TrainingArguments(
        output_dir="./output",
        num_train_epochs=5,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,
        warmup_steps=20,
        logging_steps=10,
        save_steps=50,
        fp16=True,
        optim="adamw_8bit",
        report_to="none",
    ),
)

trainer.train()

# === Cell 5: Save ===
model.save_pretrained("/content/openmythos-r16-7b")
tokenizer.save_pretrained("/content/openmythos-r16-7b")

# Download
from google.colab import files
import shutil

shutil.make_archive("/content/r16", "zip", "/content/openmythos-r16-7b")
files.download("/content/r16.zip")

print("Done! Upload the zip to Ollama for deployment.")
