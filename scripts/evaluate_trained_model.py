#!/usr/bin/env python3
"""Evaluate the trained OpenDjicht LoRA model against OpenMythos canon.

Compares:
1. Base model (Qwen2.5-1.5B-Instruct without LoRA)
2. LoRA-tuned model (Qwen2.5-1.5B + OpenDjicht LoRA)
3. RAG engine (Claude Sonnet 4.6 with few-shot)

Usage:
  python3 scripts/evaluate_trained_model.py --limit 20
"""

import json
import os
import sys
import time
import torch
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CASES_PATH = REPO_ROOT / "cases" / "corpus.jsonl"
REPORT_PATH = (
    REPO_ROOT
    / "analysis"
    / "openmythos-apex-runs"
    / "reports"
    / "MODEL_COMPARISON.json"
)

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows


def load_model(model_path, lora_path=None):
    """Load model with optional LoRA adapter."""
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import PeftModel

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )

    if lora_path:
        model = PeftModel.from_pretrained(model, lora_path)

    tokenizer = AutoTokenizer.from_pretrained(
        lora_path or model_path,
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    return model, tokenizer


def generate(model, tokenizer, prompt, max_tokens=512):
    """Generate response from model."""
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.1,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Remove prompt from response
    if response.startswith(prompt):
        response = response[len(prompt) :]
    return response.strip()


def score_response(response, expected):
    """Simple keyword overlap score."""
    if not response or not expected:
        return 0.0
    resp_words = set(response.lower().split())
    exp_words = set(expected.lower().split())
    if not exp_words:
        return 0.0
    return len(resp_words & exp_words) / len(exp_words)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--model_path", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument(
        "--lora_path", default="/mnt/data/openmythos/models/open-djicht-lora-tiny"
    )
    args = parser.parse_args()

    cases = load_jsonl(CASES_PATH)[: args.limit]

    print(f"Evaluating against {len(cases)} cases...")
    print(f"GPU: {torch.cuda.get_device_name(0)}")

    # Load base model
    print("\nLoading base model...")
    base_model, base_tokenizer = load_model(args.model_path)

    # Load LoRA model
    print("Loading LoRA model...")
    lora_model, lora_tokenizer = load_model(args.model_path, args.lora_path)

    results = []
    for i, case in enumerate(cases, 1):
        prompt = case.get("prompt", "")
        expected = case.get("expected_behavior", "")
        case_id = case.get("id", "")
        category = case.get("category", "")

        # Format prompt
        formatted = f"<|im_start|>system\nYou are an AI governance assistant.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"

        # Base model
        base_resp = generate(base_model, base_tokenizer, formatted)
        base_score = score_response(base_resp, expected)

        # LoRA model
        lora_resp = generate(lora_model, lora_tokenizer, formatted)
        lora_score = score_response(lora_resp, expected)

        improvement = lora_score - base_score

        results.append(
            {
                "case_id": case_id,
                "category": category,
                "base_score": round(base_score, 3),
                "lora_score": round(lora_score, 3),
                "improvement": round(improvement, 3),
            }
        )

        marker = "↑" if improvement > 0 else "↓" if improvement < 0 else "="
        print(
            f"  [{i:2d}/{len(cases)}] {case_id:25s} base={base_score:.2f} lora={lora_score:.2f} {marker}{abs(improvement):.2f}"
        )

    # Summary
    base_scores = [r["base_score"] for r in results]
    lora_scores = [r["lora_score"] for r in results]
    improvements = [r["improvement"] for r in results]

    print(f"\n{'=' * 60}")
    print(f"  Model Comparison Results")
    print(f"{'=' * 60}")
    print(f"  Cases: {len(results)}")
    print(f"  Base model avg:   {sum(base_scores) / len(base_scores):.2%}")
    print(f"  LoRA model avg:   {sum(lora_scores) / len(lora_scores):.2%}")
    print(f"  Improvement:      {sum(improvements) / len(improvements):+.2%}")
    print(
        f"  Wins (lora > base): {sum(1 for x in improvements if x > 0)}/{len(improvements)}"
    )

    # Per category
    by_cat = {}
    for r in results:
        cat = r["category"]
        if cat not in by_cat:
            by_cat[cat] = []
        by_cat[cat].append(r["improvement"])

    print(f"\n  Per category improvement:")
    for cat, imps in sorted(by_cat.items()):
        avg_imp = sum(imps) / len(imps)
        print(f"    {cat:25s} {avg_imp:+.2%} ({len(imps)} cases)")

    # Save
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(results, indent=2))
    print(f"\n  Saved: {REPORT_PATH}")

    # Cleanup
    del base_model, lora_model
    torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
