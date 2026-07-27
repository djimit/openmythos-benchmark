#!/bin/bash
# OpenDjicht LoRA Training on Workstation (RTX 2060 SUPER 8GB)
# Run this ON THE WORKSTATION: ssh djimit@192.168.1.28
#
# Prerequisites:
#   pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
#   pip3 install transformers peft trl datasets accelerate bitsandbytes scipy
#
# Usage (on workstation):
#   bash scripts/workstation_train.sh

set -e

# Config
BASE_MODEL="Qwen/Qwen2.5-7B-Instruct"  # Will download from HuggingFace
DATASET_PATH="/mnt/data/openmythos/openmythos-benchmark/analysis/openmythos-apex-runs/datasets/frontier-distill/sft_combined.jsonl"
OUTPUT_DIR="/mnt/data/openmythos/models/open-djicht-lora-v1"
EPOCHS=3
BATCH_SIZE=2
GRAD_ACCUM=8
LR=2e-4
LORA_R=16
LORA_ALPHA=32

echo "============================================"
echo "  OpenDjicht LoRA Training"
echo "  GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader)"
echo "  VRAM: $(nvidia-smi --query-gpu=memory.total --format=csv,noheader)"
echo "  Model: ${BASE_MODEL}"
echo "  Epochs: ${EPOCHS}"
echo "============================================"

# Create output dir
mkdir -p "${OUTPUT_DIR}"

# Run training
python3 -c "
import json, os, sys
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM, AutoTokenizer,
    TrainingArguments, BitsAndBytesConfig,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
from trl import SFTTrainer
import torch

print('Loading dataset...')
# Load SFT data
data = []
with open('${DATASET_PATH}') as f:
    for line in f:
        line = line.strip()
        if line:
            try:
                row = json.loads(line)
                msgs = row.get('messages', [])
                if len(msgs) >= 3:
                    system = msgs[0].get('content', '') if msgs[0].get('role') == 'system' else ''
                    user = msgs[1].get('content', '')
                    assistant = msgs[2].get('content', '')
                    if user and assistant:
                        text = f'<|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n{assistant}<|im_end|>'
                        data.append({'text': text})
            except:
                pass

print(f'Loaded {len(data)} training samples')
dataset = Dataset.from_list(data)

# Load model in 4-bit
print('Loading model in 4-bit...')
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type='nf4',
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    '${BASE_MODEL}',
    quantization_config=bnb_config,
    device_map='auto',
    trust_remote_code=True,
)
model.config.use_cache = False
model = prepare_model_for_kbit_training(model)

tokenizer = AutoTokenizer.from_pretrained('${BASE_MODEL}', trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# LoRA
print('Configuring LoRA...')
lora_config = LoraConfig(
    r=${LORA_R},
    lora_alpha=${LORA_ALPHA},
    lora_dropout=0.05,
    target_modules=['q_proj', 'v_proj', 'k_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj'],
    task_type=TaskType.CAUSAL_LM,
    bias='none',
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Training args
print('Starting training...')
training_args = TrainingArguments(
    output_dir='${OUTPUT_DIR}',
    num_train_epochs=${EPOCHS},
    per_device_train_batch_size=${BATCH_SIZE},
    gradient_accumulation_steps=${GRAD_ACCUM},
    learning_rate=${LR},
    warmup_ratio=0.1,
    lr_scheduler_type='cosine',
    logging_steps=5,
    save_strategy='epoch',
    fp16=True,
    optim='paged_adamw_8bit',
    report_to='none',
    max_grad_norm=0.3,
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer,
    dataset_text_field='text',
    max_seq_length=2048,
)

trainer.train()

# Save
model.save_pretrained('${OUTPUT_DIR}')
tokenizer.save_pretrained('${OUTPUT_DIR}')
print(f'Model saved to ${OUTPUT_DIR}')
print('Training complete!')
"

echo ""
echo "============================================"
echo "  Training Complete!"
echo "  Model: ${OUTPUT_DIR}"
echo "============================================"
