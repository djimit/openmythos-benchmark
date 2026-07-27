# OpenMythos R17 — Copy-paste deze hele cell in Colab
# 1. Open https://colab.research.google.com
# 2. Nieuwe notebook
# 3. Plak deze code in een cell
# 4. Runtime -> Change runtime type -> GPU -> Save
# 5. Run (2-3 uur)

import sys, subprocess, os, json, random, shutil
import torch
assert torch.cuda.is_available(), 'No GPU!'
print(f'GPU: {torch.cuda.get_device_name(0)}')
print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')

!pip install -q unsloth transformers datasets trl==0.15.2 accelerate bitsandbytes 2>&1 | tail -3

!wget -q https://raw.githubusercontent.com/djimit/openmythos-benchmark/main/analysis/openmythos-apex-runs/datasets/r17-final-sft.jsonl -O /content/r17-sft.jsonl
print(f'Dataset: {sum(1 for _ in open("/content/r17-sft.jsonl"))} examples')

from unsloth import FastLanguageModel
model, tokenizer = FastLanguageModel.from_pretrained(
    'unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit',
    max_seq_length=2048, dtype=None, load_in_4bit=True)
model = FastLanguageModel.get_peft_model(model, r=32, lora_alpha=64, lora_dropout=0.05,
    target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj'], bias='none')
print('Model loaded!')

from datasets import load_dataset
dataset = load_dataset('json', data_files='/content/r17-sft.jsonl', split='train')
dataset = dataset.map(lambda x: {'text': f'### Instruction:\n{x["instruction"]}\n\n### Response:\n{x["output"]}'})
print(f'Dataset: {len(dataset)} examples')

from trl import SFTTrainer
from transformers import TrainingArguments
trainer = SFTTrainer(
    model=model, tokenizer=tokenizer, train_dataset=dataset,
    dataset_text_field='text', max_seq_length=2048,
    args=TrainingArguments(
        output_dir='./output', num_train_epochs=5,
        per_device_train_batch_size=4, gradient_accumulation_steps=8,
        learning_rate=2e-4, warmup_steps=20, logging_steps=10,
        save_steps=100, fp16=True, optim='adamw_8bit', report_to='none'))

print('Training start (2-3 hours)...')
trainer.train()
print('Training done!')

model.save_pretrained('/content/openmythos-r17-7b')
tokenizer.save_pretrained('/content/openmythos-r17-7b')
shutil.make_archive('/content/r17', 'zip', '/content/openmythos-r17-7b')
from google.colab import files
files.download('/content/r17.zip')
print('Download started!')
