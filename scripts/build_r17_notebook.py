#!/usr/bin/env python3
"""Build a correct R17 Colab notebook .ipynb file."""

import json


def make_cell(cell_type, source, cell_id=None):
    """Create a properly formatted notebook cell."""
    if isinstance(source, str):
        lines = source.split("\n")
        source = []
        for i, line in enumerate(lines):
            if i < len(lines) - 1:
                source.append(line + "\n")
            elif line:  # last line, only add if not empty
                source.append(line + "\n")

    cell = {
        "cell_type": cell_type,
        "metadata": {"id": cell_id} if cell_id else {},
    }

    if cell_type == "code":
        cell["source"] = source
        cell["outputs"] = []
        cell["execution_count"] = None
    else:
        cell["source"] = source

    return cell


cells = []

# Cell 0: Title
cells.append(
    make_cell(
        "markdown",
        "# OpenMythos R17 — 7B QLoRA Fine-Tuning\n\n"
        "Fine-tune Qwen2.5-Coder-7B on 550 governance SFT examples.\n\n"
        "**Instructies:**\n"
        "1. Runtime → Change runtime type → GPU → Save\n"
        "2. Runtime → Run all\n"
        "3. Wacht 2-3 uur",
        "title",
    )
)

# Cell 1: GPU Check
cells.append(
    make_cell(
        "code",
        "import torch\n\n"
        "assert torch.cuda.is_available(), 'ERROR: Geen GPU! Zet runtime op GPU.'\n"
        "print(f'GPU: {torch.cuda.get_device_name(0)}')\n"
        "print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')",
        "gpu_check",
    )
)

# Cell 2: Install dependencies
cells.append(
    make_cell(
        "code",
        "# Install dependencies (2-3 minuten)\n"
        "!pip install -q unsloth transformers datasets trl==0.15.2 accelerate bitsandbytes 2>&1 | tail -5\n"
        "print('Dependencies geinstalleerd!')",
        "install",
    )
)

# Cell 3: Download dataset
cells.append(
    make_cell(
        "code",
        "# Download dataset van GitHub (550 examples)\n"
        "!wget -q https://raw.githubusercontent.com/djimit/openmythos-benchmark/main/analysis/openmythos-apex-runs/datasets/r17-final-sft.jsonl -O /content/r17-sft.jsonl\n\n"
        "count = sum(1 for _ in open('/content/r17-sft.jsonl'))\n"
        "print(f'Dataset: {count} examples')",
        "download_data",
    )
)

# Cell 4: Load model
cells.append(
    make_cell(
        "code",
        "# Laad model (4-bit QLoRA, ~2 min)\n"
        "from unsloth import FastLanguageModel\n\n"
        "model, tokenizer = FastLanguageModel.from_pretrained(\n"
        "    model_name='unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit',\n"
        "    max_seq_length=2048,\n"
        "    dtype=None,\n"
        "    load_in_4bit=True\n"
        ")\n\n"
        "model = FastLanguageModel.get_peft_model(\n"
        "    model,\n"
        "    r=32,\n"
        "    lora_alpha=64,\n"
        "    lora_dropout=0.05,\n"
        "    target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj'],\n"
        "    bias='none'\n"
        ")\n"
        "print('Model geladen!')",
        "load_model",
    )
)

# Cell 5: Prepare data
cells.append(
    make_cell(
        "code",
        "# Bereid dataset voor\n"
        "from datasets import load_dataset\n\n"
        "dataset = load_dataset('json', data_files='/content/r17-sft.jsonl', split='train')\n"
        "dataset = dataset.map(lambda x: {'text': f'### Instruction:\\n{x[\"instruction\"]}\\n\\n### Response:\\n{x[\"output\"]}'})\n"
        "print(f'Dataset klaar: {len(dataset)} examples')",
        "prepare_data",
    )
)

# Cell 6: Train
cells.append(
    make_cell(
        "code",
        "# Start training (2-3 uur op T4)\n"
        "from trl import SFTTrainer\n"
        "from transformers import TrainingArguments\n\n"
        "trainer = SFTTrainer(\n"
        "    model=model,\n"
        "    tokenizer=tokenizer,\n"
        "    train_dataset=dataset,\n"
        "    dataset_text_field='text',\n"
        "    max_seq_length=2048,\n"
        "    args=TrainingArguments(\n"
        "        output_dir='./output',\n"
        "        num_train_epochs=5,\n"
        "        per_device_train_batch_size=4,\n"
        "        gradient_accumulation_steps=8,\n"
        "        learning_rate=2e-4,\n"
        "        warmup_steps=20,\n"
        "        logging_steps=10,\n"
        "        save_steps=100,\n"
        "        fp16=True,\n"
        "        optim='adamw_8bit',\n"
        "        report_to='none'\n"
        "    )\n"
        ")\n\n"
        "print('Training start (2-3 uur)...')\n"
        "trainer.train()\n"
        "print('Training voltooid!')",
        "train",
    )
)

# Cell 7: Save & Download
cells.append(
    make_cell(
        "code",
        "# Opslaan en downloaden\n"
        "model.save_pretrained('/content/openmythos-r17-7b')\n"
        "tokenizer.save_pretrained('/content/openmythos-r17-7b')\n\n"
        "import shutil\n"
        "from google.colab import files\n\n"
        "shutil.make_archive('/content/r17', 'zip', '/content/openmythos-r17-7b')\n"
        "files.download('/content/r17.zip')\n"
        "print('Download gestart!')",
        "save_download",
    )
)

# Build notebook
notebook = {
    "cells": cells,
    "metadata": {
        "accelerator": "GPU",
        "colab": {"gpuType": "T4", "private_outputs": True, "provenance": []},
        "kernelspec": {
            "display_name": "Python 3 (ipykernel)",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.10.12"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

output_path = "notebooks/openmythos_r17_all_in_one.ipynb"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

print(f"Notebook geschreven: {output_path}")
print(f"Cells: {len(cells)}")
for i, cell in enumerate(cells):
    src = cell["source"]
    n_lines = len(src)
    first = src[0].rstrip()[:60] if src else ""
    print(f"  Cell {i} ({cell['cell_type']:8s}): {n_lines:2d} regels | {first}")
