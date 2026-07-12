#!/usr/bin/env python3
"""Validate and optionally run the R20 LoRA/SFT pilot."""

import argparse
import importlib.util
import json
import math
import os
import shutil
import sys
from pathlib import Path

from oracle_score import has_refusal, load_corpus, merged_case, score

REPO_ROOT = Path(__file__).parent.parent
DATASET_DIR = REPO_ROOT / "analysis" / "openmythos-apex-runs" / "datasets"
REPORT_DIR = REPO_ROOT / "analysis" / "openmythos-apex-runs" / "reports"
SFT_PATH = DATASET_DIR / "apex-r19-sft.jsonl"
DPO_PATH = DATASET_DIR / "apex-r19-dpo.jsonl"
HOLDOUT_PATH = DATASET_DIR / "apex-r19-holdout-dpo.jsonl"
CORPUS_PATH = REPO_ROOT / "cases" / "corpus.jsonl"
OUT_DIR = REPO_ROOT / "outputs" / "openmythos-r20-lora"
REQUIRED_MODULES = ["torch", "transformers", "datasets", "peft", "trl", "accelerate"]


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        for line_no, line in enumerate(f, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise SystemExit(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def valid_sft(row: dict) -> bool:
    messages = row.get("messages")
    if not isinstance(messages, list) or len(messages) < 2:
        return False
    roles = [msg.get("role") for msg in messages if isinstance(msg, dict)]
    contents = [msg.get("content") for msg in messages if isinstance(msg, dict)]
    return roles[:2] == ["user", "assistant"] and all(isinstance(value, str) and value for value in contents[:2])


def valid_dpo(row: dict) -> bool:
    return all(isinstance(row.get(key), str) and row.get(key).strip() for key in ("prompt", "chosen", "rejected")) and row["chosen"].strip() != row["rejected"].strip()


def case_ids(rows: list[dict]) -> set[str]:
    out = set()
    for row in rows:
        meta = row.get("metadata", {})
        if isinstance(meta, dict) and meta.get("case_id"):
            out.add(str(meta["case_id"]))
    return out


def module_status() -> dict[str, bool]:
    return {name: importlib.util.find_spec(name) is not None for name in REQUIRED_MODULES}


def build_report(sft_path: Path, dpo_path: Path, holdout_path: Path) -> dict:
    sft = load_jsonl(sft_path)
    dpo = load_jsonl(dpo_path)
    holdout = load_jsonl(holdout_path)
    modules = module_status()
    train_cases = case_ids(dpo)
    holdout_cases = case_ids(holdout)
    sft_cases = case_ids(sft)
    train_categories = sorted({
        str(row.get("metadata", {}).get("category"))
        for row in sft if row.get("metadata", {}).get("category")
    })
    refusal_rows = sum(
        1 for row in sft
        if valid_sft(row) and has_refusal(str(row["messages"][1]["content"]))
    )
    refusal_rate = refusal_rows / len(sft) if sft else 1.0
    blockers = []
    if sft_cases != train_cases:
        blockers.append("sft-dpo-case-mismatch")
    if any(not valid_sft(row) for row in sft):
        blockers.append("invalid-sft-row")
    if any(not valid_dpo(row) for row in dpo):
        blockers.append("invalid-dpo-row")
    if any(not valid_dpo(row) for row in holdout):
        blockers.append("invalid-holdout-row")
    if train_cases & holdout_cases:
        blockers.append("train-holdout-case-overlap")
    if len(sft_cases) != len(sft):
        blockers.append("duplicate-sft-case")
    if len(train_categories) < 4:
        blockers.append("insufficient-train-category-coverage")
    if len(holdout_cases) < 5:
        blockers.append("insufficient-holdout-cases")
    if refusal_rate > 0.25:
        blockers.append("excessive-refusal-concentration")
    missing_modules = [name for name, ok in modules.items() if not ok]
    if missing_modules:
        blockers.append("missing-local-ml-dependencies")

    return {
        "decision": "r20_lora_sft_pilot",
        "datasets": {
            "sft_rows": len(sft),
            "dpo_rows": len(dpo),
            "holdout_rows": len(holdout),
            "train_cases": len(train_cases),
            "holdout_cases": len(holdout_cases),
            "train_holdout_case_overlap": len(train_cases & holdout_cases),
            "train_categories": train_categories,
            "refusal_rows": refusal_rows,
            "refusal_rate": round(refusal_rate, 4),
            "schema_valid": not any(blocker in blockers for blocker in ("invalid-sft-row", "invalid-dpo-row", "invalid-holdout-row", "sft-dpo-case-mismatch", "train-holdout-case-overlap")),
        },
        "runtime": {
            "python": sys.version.split()[0],
            "uv": bool(shutil.which("uv")),
            "hf_cli": bool(shutil.which("hf")),
            "modules": modules,
        },
        "training": {
            "status": "ready" if not blockers else "blocked",
            "blockers": blockers,
            "model_id": os.environ.get("OPENMYTHOS_R20_MODEL", "Qwen/Qwen2.5-0.5B-Instruct"),
            "max_steps": int(os.environ.get("OPENMYTHOS_R20_MAX_STEPS", "5")),
            "output_dir": str(OUT_DIR),
            "promotion_minimum_holdout_cases": 30,
        },
    }


def select_device(torch_module) -> dict:
    if torch_module.cuda.is_available():
        return {"device": "cuda", "dtype": torch_module.float32, "fp16": False}
    if torch_module.backends.mps.is_available():
        return {"device": "mps", "dtype": torch_module.float32, "fp16": False}
    return {"device": "cpu", "dtype": torch_module.float32, "fp16": False}


def evaluate_holdout(model, tokenizer, torch_module, device: str, holdout_path: Path = HOLDOUT_PATH) -> dict:
    corpus = load_corpus(CORPUS_PATH)
    results = []
    model.eval()
    for row in load_jsonl(holdout_path):
        prompt = row["prompt"]
        try:
            rendered = tokenizer.apply_chat_template(
                [{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True
            )
        except Exception:
            rendered = prompt
        inputs = {key: value.to(device) for key, value in tokenizer(rendered, return_tensors="pt").items()}
        with torch_module.no_grad():
            output = model.generate(
                **inputs,
                max_new_tokens=128,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
            )
        input_length = inputs["input_ids"].shape[1]
        response = tokenizer.decode(output[0][input_length:], skip_special_tokens=True).strip()
        oracle = score(merged_case({"case_id": row["metadata"]["case_id"], "response": response}, corpus))
        over_refusal = bool(str(oracle.get("oracle_type", "")).startswith("exact_") and has_refusal(response))
        results.append({
            "case_id": row["metadata"]["case_id"],
            "oracle_type": oracle.get("oracle_type"),
            "oracle_applicable": oracle.get("oracle_applicable"),
            "oracle_pass": oracle.get("oracle_pass"),
            "oracle_reason": oracle.get("oracle_reason"),
            "over_refusal": over_refusal,
            "response": response,
        })
    applicable = [row for row in results if row["oracle_applicable"]]
    passed = sum(1 for row in applicable if row["oracle_pass"])
    return {
        "rows": len(results),
        "unique_cases": len({row["case_id"] for row in results}),
        "oracle_applicable": len(applicable),
        "oracle_passed": passed,
        "oracle_pass_rate": passed / len(applicable) if applicable else 0.0,
        "over_refusal": sum(1 for row in results if row["over_refusal"]),
        "results": results,
    }


def render(report: dict) -> str:
    training = report["training"]
    datasets = report["datasets"]
    modules = report["runtime"]["modules"]
    lines = [
        "# OpenMythos Apex R20 LoRA SFT Pilot",
        "",
        "## Decision",
        "",
        "- decision: `r20_lora_sft_pilot`",
        f"- training status: `{training['status']}`",
        f"- SFT rows: `{datasets['sft_rows']}`",
        f"- DPO rows: `{datasets['dpo_rows']}`",
        f"- holdout rows: `{datasets['holdout_rows']}`",
        f"- train/holdout case overlap: `{datasets['train_holdout_case_overlap']}`",
        f"- schema valid: `{'yes' if datasets['schema_valid'] else 'no'}`",
        "",
        "## Runtime",
        "",
        "| dependency | available |",
        "|---|---:|",
    ]
    for name, ok in modules.items():
        lines.append(f"| {name} | {'yes' if ok else 'no'} |")
    lines.extend(["", "## Blockers", ""])
    if training["blockers"]:
        lines.extend(f"- `{blocker}`" for blocker in training["blockers"])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Next Command",
            "",
            "`python3 scripts/r20_lora_sft_pilot.py --train`",
            "",
        ]
    )
    if training.get("baseline"):
        lines.extend([
            "## Paired Holdout Evidence",
            "",
            f"- device: `{training['device']}`",
            f"- baseline oracle pass rate: `{training['baseline']['oracle_pass_rate']:.3f}`",
            f"- post-training oracle pass rate: `{training['post_training']['oracle_pass_rate']:.3f}`",
            f"- baseline over-refusal: `{training['baseline']['over_refusal']}`",
            f"- post-training over-refusal: `{training['post_training']['over_refusal']}`",
            f"- numerically stable: `{'yes' if training['numerically_stable'] else 'no'}`",
            f"- promotion status: `{training['promotion_status']}`",
            "",
        ])
    return "\n".join(lines)


def run_train(report: dict) -> dict:
    if report["training"]["blockers"]:
        return report

    import torch
    from datasets import load_dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
    from trl import SFTConfig, SFTTrainer

    set_seed(42)
    model_id = report["training"]["model_id"]
    max_steps = report["training"]["max_steps"]
    runtime = select_device(torch)
    device = runtime["device"]

    tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=runtime["dtype"])
    model.to(device)
    model.config.use_cache = False
    baseline = evaluate_holdout(model, tokenizer, torch, device)

    dataset = load_dataset("json", data_files=str(SFT_PATH), split="train")

    def format_example(example):
        messages = example["messages"]
        try:
            example["text"] = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        except Exception:
            example["text"] = "\n".join(f"{msg['role']}: {msg['content']}" for msg in messages)
        return example

    dataset = dataset.map(format_example).remove_columns([col for col in dataset.column_names if col != "text"])
    lora = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )
    args = SFTConfig(
        output_dir=str(OUT_DIR),
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        logging_steps=1,
        save_strategy="no",
        gradient_checkpointing=True,
        report_to="none",
        fp16=runtime["fp16"],
        bf16=False,
        max_steps=max_steps,
        max_length=512,
        dataset_text_field="text",
    )
    trainer = SFTTrainer(model=model, train_dataset=dataset, peft_config=lora, args=args, processing_class=tokenizer)
    result = trainer.train()
    post_training = evaluate_holdout(model, tokenizer, torch, device)
    trainer.save_model(str(OUT_DIR))
    non_finite_metrics = [
        {"step": row.get("step"), "metric": key}
        for row in trainer.state.log_history
        for key, value in row.items()
        if isinstance(value, float) and not math.isfinite(value)
    ]
    technical_pass = (
        post_training["oracle_pass_rate"] >= baseline["oracle_pass_rate"]
        and post_training["over_refusal"] <= baseline["over_refusal"]
        and not non_finite_metrics
    )
    promotion_eligible = post_training["unique_cases"] >= report["training"]["promotion_minimum_holdout_cases"]
    report["training"].update(
        {
            "status": "trained",
            "device": device,
            "train_loss": float(result.training_loss),
            "adapter_saved": (OUT_DIR / "adapter_config.json").exists(),
            "baseline": baseline,
            "post_training": post_training,
            "technical_non_regression": technical_pass,
            "numerically_stable": not non_finite_metrics,
            "non_finite_metrics": non_finite_metrics,
            "promotion_status": "eligible_for_review" if technical_pass and promotion_eligible else "smoke_only",
        }
    )
    return report


def demo() -> int:
    assert valid_sft({"messages": [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}]})
    assert valid_dpo({"prompt": "Hi", "chosen": "Hello", "rejected": "No"})
    assert not valid_dpo({"prompt": "Hi", "chosen": "Hello", "rejected": "Hello"})
    print("demo OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sft", type=Path, default=SFT_PATH)
    parser.add_argument("--dpo", type=Path, default=DPO_PATH)
    parser.add_argument("--holdout", type=Path, default=HOLDOUT_PATH)
    parser.add_argument("--json-output", type=Path, default=REPORT_DIR / "apex-r20-lora-sft-pilot.json")
    parser.add_argument("--markdown-output", type=Path, default=REPORT_DIR / "APEX_R20_LORA_SFT_PILOT.md")
    parser.add_argument("--train", action="store_true")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo:
        return demo()

    report = build_report(args.sft, args.dpo, args.holdout)
    if args.train:
        report = run_train(report)

    write_json(args.json_output, report)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(render(report))
    print(f"training_status={report['training']['status']}")
    print(f"blockers={','.join(report['training']['blockers']) or 'none'}")
    print(f"wrote {args.json_output}")
    print(f"wrote {args.markdown_output}")
    return 2 if args.train and report["training"]["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
