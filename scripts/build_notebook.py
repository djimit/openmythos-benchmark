#!/usr/bin/env python3
"""Build R17 Colab notebook with correct format."""

import json

cells = []

# Cell 0: Title
cells.append(
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# OpenMythos R17 — 7B QLoRA Fine-Tuning\n",
            "\n",
            "1. Runtime → Change runtime type → GPU → Save\n",
            "2. Runtime → Run all\n",
            "3. Wait 2-3 hours",
        ],
    }
)

# Cell 1: GPU check
cells.append(
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import torch\n",
            "assert torch.cuda.is_available(), 'No GPU!'\n",
            "print(f'GPU: {torch.cuda.get_device_name(0)}')\n",
            "print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')",
        ],
    }
)

# Cell 2: Install
cells.append(
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "!pip install -q unsloth transformers datasets trl==0.15.2 accelerate bitsandbytes 2>&1 | tail -3\n",
            "print('Done!')",
        ],
    }
)

# Cell 3: Download data
cells.append(
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "!wget -q https://raw.githubusercontent.com/djimit/openmythos-benchmark/main/analysis/openmythos-apex-runs/datasets/r17-final-sft.jsonl -O /content/r17-sft.jsonl\n",
            "count = sum(1 for _ in open('/content/r17-sft.jsonl'))\n",
            "print(f'Dataset: {count} examples')",
        ],
    }
)

# Cell 4: Load model
cells.append(
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "from unsloth import FastLanguageModel\n",
            "model, tokenizer = FastLanguageModel.from_pretrained(\n",
            "    model_name='unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit',\n",
            "    max_seq_length=2048, dtype=None, load_in_4bit=True)\n",
            "model = FastLanguageModel.get_peft_model(model, r=32, lora_alpha=64, lora_dropout=0.05,\n",
            "    target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj'], bias='none')\n",
            "print('Model loaded!')",
        ],
    }
)

# Cell 5: Prepare data
cells.append(
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "from datasets import load_dataset\n",
            "dataset = load_dataset('json', data_files='/content/r17-sft.jsonl', split='train')\n",
            "dataset = dataset.map(lambda x: {'text': f'### Instruction:\\n{x[\"instruction\"]}\\n\\n### Response:\\n{x[\"output\"]}'})\n",
            "print(f'Dataset: {len(dataset)} examples')",
        ],
    }
)

# Cell 6: Train
cells.append(
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "from trl import SFTTrainer\n",
            "from transformers import TrainingArguments\n",
            "trainer = SFTTrainer(\n",
            "    model=model, tokenizer=tokenizer, train_dataset=dataset,\n",
            "    dataset_text_field='text', max_seq_length=2048,\n",
            "    args=TrainingArguments(\n",
            "        output_dir='./output', num_train_epochs=5,\n",
            "        per_device_train_batch_size=4, gradient_accumulation_steps=8,\n",
            "        learning_rate=2e-4, warmup_steps=20, logging_steps=10,\n",
            "        save_steps=100, fp16=True, optim='adamw_8bit', report_to='none'))\n",
            "print('Training start (2-3 hours)...')\n",
            "trainer.train()\n",
            "print('Training done!')",
        ],
    }
)

# Cell 7: Save & download
cells.append(
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "model.save_pretrained('/content/openmythos-r17-7b')\n",
            "tokenizer.save_pretrained('/content/openmythos-r17-7b')\n",
            "import shutil\n",
            "from google.colab import files\n",
            "shutil.make_archive('/content/r17', 'zip', '/content/openmythos-r17-7b')\n",
            "files.download('/content/r17.zip')\n",
            "print('Download started!')",
        ],
    }
)

nb = {
    "cells": cells,
    "metadata": {
        "accelerator": "GPU",
        "colab": {"gpuType": "T4", "private_outputs": True},
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 4,
}

output = "notebooks/openmythos_r17_all_in_one.ipynb"
with open(output, "w") as f:
    json.dump(nb, f, indent=1)

print(f"Written {len(cells)} cells to {output}")

# Verify
with open(output) as f:
    nb2 = json.load(f)
for i, c in enumerate(nb2["cells"]):
    src = c["source"]
    print(f"  Cell {i}: {c['cell_type']}, {len(src)} lines")
