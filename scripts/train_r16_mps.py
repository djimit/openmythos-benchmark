#!/usr/bin/env python3
"""R16 7B QLoRA training on MacBook Apple Silicon (MPS) via Unsloth.

Uses MLX backend for native Apple Silicon support.
Requires: pip install unsloth mlx mlx-lm

Usage:
    python3 scripts/train_r16_mps.py
"""

import os, json
from pathlib import Path

DATASET = Path("analysis/openmythos-apex-runs/datasets/r15-merged-sft.jsonl")
OUTPUT = Path("models/r16-qlora-7b")


def main():
    import mlx.core as mx
    from mlx_lm.tuner import run, load
    from mlx_lm.tuner.utils import linear_to_lora_layers
    from mlx_lm.utils import load as load_model

    MODEL_NAME = "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit"
    MAX_SEQ_LEN = 2048

    print(f"Loading model: {MODEL_NAME}")
    model, tokenizer = load_model(MODEL_NAME)

    # LoRA config
    lora_config = {
        "rank": 32,
        "alpha": 64,
        "dropout": 0.05,
        "keys": [
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
    }
    linear_to_lora_layers(model, num_layers=24, config=lora_config)

    # Load data
    data = []
    with open(DATASET) as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))

    def fmt(ex):
        return f"### Instruction:\n{ex['instruction']}\n\n### Response:\n{ex['output']}"

    train_texts = [fmt(ex) for ex in data]
    print(f"Dataset: {len(train_texts)} examples")

    # Training args
    training_args = {
        "model": MODEL_NAME,
        "data": train_texts,
        "batch_size": 2,
        "iters": len(train_texts) * 5 // 2,  # 5 epochs
        "val_batches": 0,
        "learning_rate": 2e-4,
        "steps_per_report": 10,
        "steps_per_save": 50,
        "adapter_path": str(OUTPUT / "adapters"),
        "max_seq_length": MAX_SEQ_LEN,
    }

    print(f"Starting R16 training on MPS...")
    print(f"Iterations: {training_args['iters']}")

    # Run training
    run(model, tokenizer, training_args)

    # Save
    model.save_weights(str(OUTPUT / "adapters.npz"))
    print(f"Saved to {OUTPUT}")

    # Metadata
    meta = {
        "run": "R16",
        "base_model": MODEL_NAME,
        "examples": len(train_texts),
        "epochs": 5,
        "lora_r": 32,
        "device": "Apple Silicon MPS/MLX",
    }
    (OUTPUT / "training_meta.json").write_text(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
