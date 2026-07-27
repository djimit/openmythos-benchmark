#!/usr/bin/env python3
"""Collect frontier-model responses from existing traces into SFT/DPO training data.

Scans all trace files in traces/ for frontier-model outputs (claude-fable-5,
claude-opus-4-8, gpt-5, gemini-2.5-pro, gpt-oss:20b) and converts them into:
  - SFT format: {messages: [{role: user, content: prompt}, {role: assistant, content: response}]}
  - DPO format: {prompt, chosen (frontier), rejected (open_source), category}

This is the first step toward OpenDjicht-1: distill frontier capabilities
into training data for a smaller open-weight model.

Usage:
  python3 scripts/frontier_distill_collector.py
  python3 scripts/frontier_distill_collector.py --dry-run
  python3 scripts/frontier_distill_collector.py --min-judge-score 3
"""

import argparse
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
TRACES_DIR = REPO_ROOT / "traces"
DATASET_DIR = (
    REPO_ROOT / "analysis" / "openmythos-apex-runs" / "datasets" / "frontier-distill"
)
CORPUS_PATH = REPO_ROOT / "cases" / "corpus.jsonl"

FRONTIER_MODELS = {
    "claude-fable-5",
    "claude-opus-4-8",
    "claude-opus-4-7",
    "claude-sonnet",
    "gpt-5",
    "gpt-4o",
    "gpt-4.1",
    "gemini-2.5-pro",
    "gemini-2.5",
    "gpt-oss:20b",
    "gpt-oss_20b",
}

OPEN_SOURCE_MODELS = {
    "qwen2.5-coder:14b",
    "qwen2.5-coder:7b",
    "qwen2.5:14b",
    "qwen2.5:32b",
    "llama3.1:8b",
    "qwen2_5_coder_14b",
    "qwen2_5_coder_7b",
    "qwen2_5_coder_latest",
    "gpt-oss:20b",
    "gpt_oss_20b",
}


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def is_frontier(model_name: str) -> bool:
    normalized = model_name.strip().lower()
    for fm in FRONTIER_MODELS:
        if fm.lower() in normalized or normalized in fm.lower():
            return True
    return False


def is_open_source(model_name: str) -> bool:
    normalized = model_name.strip().lower()
    for om in OPEN_SOURCE_MODELS:
        if om.lower() in normalized or normalized in om.lower():
            return True
    return False


def load_corpus() -> dict[str, dict]:
    cases = {}
    if not CORPUS_PATH.exists():
        return cases
    for row in load_jsonl(CORPUS_PATH):
        cases[row.get("case_id", "")] = row
    return cases


def scan_traces() -> dict[str, list[dict]]:
    """Scan all trace files, group by case_id, separate frontier vs open-source."""
    frontier_responses = defaultdict(list)
    open_source_responses = defaultdict(list)

    trace_files = list(TRACES_DIR.rglob("*.jsonl"))
    scanned = 0

    for trace_file in trace_files:
        rows = load_jsonl(trace_file)
        scanned += 1

        for row in rows:
            model = row.get("model", "")
            case_id = row.get("case_id", "")
            response = row.get("response", "")

            if not case_id or not response or not response.strip():
                continue

            entry = {
                "case_id": case_id,
                "model": model,
                "response": response,
                "prompt": row.get("prompt", ""),
                "category": row.get("category", ""),
                "judge_score": row.get("judge_score"),
                "oracle_pass": row.get("oracle_pass"),
                "oracle_type": row.get("oracle_type"),
                "source_file": str(trace_file.relative_to(REPO_ROOT)),
                "expected_behavior": row.get("expected_behavior", ""),
            }

            if is_frontier(model):
                frontier_responses[case_id].append(entry)
            elif is_open_source(model):
                open_source_responses[case_id].append(entry)

    return {
        "frontier": dict(frontier_responses),
        "open_source": dict(open_source_responses),
        "scanned_files": scanned,
    }


def build_sft_data(
    frontier_responses: dict, min_judge_score: float | None = None
) -> list[dict]:
    """Build SFT samples from frontier-model responses."""
    sft_rows = []
    seen = set()

    for case_id, responses in frontier_responses.items():
        for resp in responses:
            judge_score = resp.get("judge_score")
            if min_judge_score is not None and judge_score is not None:
                try:
                    if float(judge_score) < min_judge_score:
                        continue
                except (ValueError, TypeError):
                    pass

            prompt = resp.get("prompt", "")
            response = resp.get("response", "")
            if not prompt.strip() or not response.strip():
                continue

            dedup_key = hashlib.sha256(
                f"{resp['model']}::{prompt}::{response[:200]}".encode()
            ).hexdigest()[:16]
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            sft_rows.append(
                {
                    "id": f"sft-{dedup_key}",
                    "case_id": case_id,
                    "category": resp.get("category", ""),
                    "source_model": resp["model"],
                    "messages": [
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": response},
                    ],
                    "judge_score": judge_score,
                    "oracle_pass": resp.get("oracle_pass"),
                    "split": "train" if int(dedup_key[:4], 16) % 5 != 0 else "holdout",
                }
            )

    return sft_rows


def build_dpo_data(
    frontier_responses: dict,
    open_source_responses: dict,
) -> list[dict]:
    """Build DPO pairs: frontier=chosen, open_source=rejected, same case_id."""
    dpo_rows = []
    seen = set()

    for case_id in frontier_responses:
        if case_id not in open_source_responses:
            continue

        best_frontier = None
        best_frontier_score = -1
        for resp in frontier_responses[case_id]:
            score = resp.get("judge_score")
            try:
                score = float(score) if score is not None else 0
            except (ValueError, TypeError):
                score = 0
            if score > best_frontier_score:
                best_frontier_score = score
                best_frontier = resp

        best_open_source = None
        best_open_source_score = -1
        for resp in open_source_responses[case_id]:
            score = resp.get("judge_score")
            try:
                score = float(score) if score is not None else 0
            except (ValueError, TypeError):
                score = 0
            if score > best_open_source_score:
                best_open_source_score = score
                best_open_source = resp

        if not best_frontier or not best_open_source:
            continue

        prompt = best_frontier.get("prompt", "")
        chosen = best_frontier.get("response", "")
        rejected = best_open_source.get("response", "")

        if not prompt.strip() or not chosen.strip() or not rejected.strip():
            continue
        if chosen.strip() == rejected.strip():
            continue

        dedup_key = hashlib.sha256(
            f"dpo-{case_id}-{best_frontier['model']}-{best_open_source['model']}".encode()
        ).hexdigest()[:16]
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        dpo_rows.append(
            {
                "id": f"dpo-{dedup_key}",
                "case_id": case_id,
                "category": best_frontier.get("category", ""),
                "prompt": prompt,
                "chosen": chosen,
                "chosen_model": best_frontier["model"],
                "chosen_score": best_frontier_score,
                "rejected": rejected,
                "rejected_model": best_open_source["model"],
                "rejected_score": best_open_source_score,
                "expected_behavior": best_frontier.get("expected_behavior", ""),
                "split": "train" if int(dedup_key[:4], 16) % 5 != 0 else "holdout",
            }
        )

    return dpo_rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect frontier-model training data from traces"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Report stats without writing files"
    )
    parser.add_argument(
        "--min-judge-score",
        type=float,
        default=None,
        help="Minimum judge score for SFT",
    )
    args = parser.parse_args()

    print(f"Scanning traces in {TRACES_DIR.relative_to(REPO_ROOT)}...")
    scan = scan_traces()
    frontier = scan["frontier"]
    open_source = scan["open_source"]

    print(f"  Scanned {scan['scanned_files']} trace files")
    print(
        f"  Frontier responses: {sum(len(v) for v in frontier.values())} across {len(frontier)} cases"
    )
    print(
        f"  Open-source responses: {sum(len(v) for v in open_source.values())} across {len(open_source)} cases"
    )

    sft = build_sft_data(frontier, args.min_judge_score)
    dpo = build_dpo_data(frontier, open_source)

    sft_train = sum(1 for r in sft if r["split"] == "train")
    sft_holdout = sum(1 for r in sft if r["split"] == "holdout")
    dpo_train = sum(1 for r in dpo if r["split"] == "train")
    dpo_holdout = sum(1 for r in dpo if r["split"] == "holdout")

    print(f"\nSFT samples: {len(sft)} (train={sft_train}, holdout={sft_holdout})")
    print(f"DPO pairs: {len(dpo)} (train={dpo_train}, holdout={dpo_holdout})")

    if sft:
        sft_by_model = Counter(r["source_model"] for r in sft)
        print(f"\n  SFT by source model:")
        for model, count in sft_by_model.most_common():
            print(f"    {model}: {count}")

        sft_by_cat = Counter(r["category"] for r in sft)
        print(f"\n  SFT by category:")
        for cat, count in sft_by_cat.most_common():
            print(f"    {cat}: {count}")

    if dpo:
        dpo_by_cat = Counter(r["category"] for r in dpo)
        print(f"\n  DPO by category:")
        for cat, count in dpo_by_cat.most_common():
            print(f"    {cat}: {count}")

    if args.dry_run:
        print("\n[DRY RUN — no files written]")
        return 0

    if sft:
        write_jsonl(DATASET_DIR / "sft.jsonl", sft)
        print(f"\n  Wrote {DATASET_DIR / 'sft.jsonl'}")

    if dpo:
        write_jsonl(DATASET_DIR / "dpo.jsonl", dpo)
        print(f"  Wrote {DATASET_DIR / 'dpo.jsonl'}")

    manifest = {
        "generated_at": str(Path.cwd()),
        "scanned_files": scan["scanned_files"],
        "frontier_cases": len(frontier),
        "open_source_cases": len(open_source),
        "sft_samples": len(sft),
        "sft_train": sft_train,
        "sft_holdout": sft_holdout,
        "dpo_pairs": len(dpo),
        "dpo_train": dpo_train,
        "dpo_holdout": dpo_holdout,
        "sft_by_model": dict(Counter(r["source_model"] for r in sft)),
        "sft_by_category": dict(Counter(r["category"] for r in sft)),
        "dpo_by_category": dict(Counter(r["category"] for r in dpo)),
    }
    write_jsonl(DATASET_DIR / "manifest.json", [manifest])
    print(f"  Wrote {DATASET_DIR / 'manifest.json'}")

    print(f"\nDone. Next step: review quality, then train with r20_lora_sft_pilot.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
