#!/usr/bin/env python3
"""Compare pre-registered Qwen2.5 capacities on consumed development cases."""

import argparse
import hashlib
import json
import time
from pathlib import Path

from oracle_score import infer_oracle, load_corpus, merged_case
from r20_lora_sft_pilot import DATASET_DIR, REPORT_DIR, evaluate_holdout, load_jsonl

CANDIDATES = [
    "Qwen/Qwen2.5-0.5B-Instruct",
    "Qwen/Qwen2.5-1.5B-Instruct",
    "Qwen/Qwen2.5-3B-Instruct",
]
MANIFESTS = [
    DATASET_DIR / "apex-r21-holdout.jsonl",
    DATASET_DIR / "apex-r21-confirmatory-holdout.jsonl",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_manifests(paths: list[Path]) -> tuple[int, int]:
    corpus = load_corpus(Path(__file__).parent.parent / "cases" / "corpus.jsonl")
    rows = [row for path in paths for row in load_jsonl(path)]
    ids = [str(row.get("metadata", {}).get("case_id")) for row in rows]
    categories = {row.get("metadata", {}).get("category") for row in rows}
    if len(rows) != 60 or len(set(ids)) != 60 or len(categories) != 8:
        raise SystemExit("blocked: invalid-development-coverage")
    missing = [
        case_id for case_id, row in zip(ids, rows)
        if not infer_oracle(merged_case({**row, "case_id": case_id}, corpus))[0]
    ]
    if missing:
        raise SystemExit(f"blocked: missing-oracle:{','.join(missing)}")
    return len(rows), len(categories)


def combine(parts: list[dict]) -> dict:
    results = [row for part in parts for row in part["results"]]
    applicable = [row for row in results if row["oracle_applicable"]]
    passed = sum(bool(row["oracle_pass"]) for row in applicable)
    return {
        "rows": len(results),
        "unique_cases": len({row["case_id"] for row in results}),
        "oracle_applicable": len(applicable),
        "oracle_passed": passed,
        "oracle_pass_rate": passed / len(applicable) if applicable else 0.0,
        "canary_failures": sum(
            1 for row in applicable if row["case_id"].startswith("canary-") and not row["oracle_pass"]
        ),
        "over_refusal": sum(int(row["over_refusal"]) for row in results),
        "results": results,
    }


def select_candidate(results: list[dict]) -> dict:
    successful = [row for row in results if row.get("evaluation")]
    baseline = next((row for row in successful if row["model_id"] == CANDIDATES[0]), None)
    if not baseline:
        return {"status": "stop_local_lora", "selected_model": None, "reasons": ["missing-baseline"]}
    base = baseline["evaluation"]
    valid = [
        row for row in successful[1:]
        if row["evaluation"]["oracle_passed"] >= base["oracle_passed"] + 6
        and row["evaluation"]["canary_failures"] <= base["canary_failures"]
        and row["evaluation"]["unique_cases"] == 60
        and row["evaluation"]["oracle_applicable"] == 60
    ]
    if not valid:
        return {"status": "stop_local_lora", "selected_model": None, "reasons": ["no-capacity-candidate-qualified"]}
    best = max(row["evaluation"]["oracle_passed"] for row in valid)
    selected = next(row for row in valid if row["evaluation"]["oracle_passed"] >= best - 2)
    return {"status": "selected", "selected_model": selected["model_id"], "reasons": []}


def evaluate_model(model_id: str, manifests: list[Path]) -> dict:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, __version__, set_seed

    started = time.time()
    set_seed(42)
    tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(model_id, dtype=torch.float16)
    model.to("cuda")
    model.eval()
    model.config.use_cache = True
    revision = getattr(model.config, "_commit_hash", None)
    parts = [evaluate_holdout(model, tokenizer, torch, "cuda", path) for path in manifests]
    evaluation = combine(parts)
    del model, tokenizer
    torch.cuda.empty_cache()
    return {
        "model_id": model_id,
        "revision": revision,
        "transformers": __version__,
        "duration_seconds": round(time.time() - started, 3),
        "evaluation": evaluation,
    }


def render(report: dict) -> str:
    lines = ["# OpenMythos R24 Capacity Selection", ""]
    for row in report["candidates"]:
        result = row.get("evaluation")
        if result:
            lines.append(
                f"- `{row['model_id']}`: {result['oracle_passed']}/60, "
                f"canary failures {result['canary_failures']}, over-refusal {result['over_refusal']}"
            )
        else:
            lines.append(f"- `{row['model_id']}`: error `{row['error']}`")
    lines.extend([
        "",
        f"Decision: `{report['decision']['status']}`",
        f"Selected model: `{report['decision']['selected_model'] or 'none'}`",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=REPORT_DIR / "apex-r24-capacity-selection.json")
    parser.add_argument("--markdown-output", type=Path, default=REPORT_DIR / "APEX_R24_CAPACITY_SELECTION.md")
    args = parser.parse_args()
    case_count, category_count = validate_manifests(MANIFESTS)
    candidates = []
    for model_id in CANDIDATES:
        try:
            candidates.append(evaluate_model(model_id, MANIFESTS))
        except Exception as exc:
            candidates.append({"model_id": model_id, "error": f"{type(exc).__name__}: {exc}"})
    report = {
        "schema_version": 1,
        "case_count": case_count,
        "category_count": category_count,
        "decoding": {"dtype": "float16", "do_sample": False, "max_new_tokens": 128, "seed": 42},
        "manifests_sha256": {path.name: sha256(path) for path in MANIFESTS},
        "candidates": candidates,
        "decision": select_candidate(candidates),
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(render(report))
    print(render(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
