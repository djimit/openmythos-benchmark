#!/usr/bin/env python3
"""Probabilistic LLM-as-judge: 3 runs per case, take median score.

Reduces judge noise by running the same case 3 times and taking the median.
Also reports agreement (all same = high confidence, mixed = low confidence).

Usage:
  python3 scripts/judge_probabilistic.py --trace traces/eval.jsonl --corpus cases/corpus.jsonl \
      --judge-model openai-gpt5 --judge-backend openai --judge-url "http://192.168.1.28:4000/v1" \
      --output traces/judged_prob.jsonl --runs 3 --strict
"""

import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def run_judge_once(
    trace_path,
    corpus_path,
    judge_model,
    judge_backend,
    judge_url,
    output_dir,
    run_id,
    strict=False,
):
    """Run judge once, return output file path."""
    stem = trace_path.stem
    out = output_dir / f"{stem}_run{run_id}.jsonl"
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "judge.py"),
        "--trace",
        str(trace_path),
        "--corpus",
        str(corpus_path),
        "--judge-model",
        judge_model,
        "--judge-backend",
        judge_backend,
        "--output",
        str(out),
    ]
    if judge_url:
        cmd += ["--judge-url", judge_url]
    if strict:
        cmd.append("--strict")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Judge run {run_id} failed: {result.stderr[:200]}", file=sys.stderr)
    return out


def load_scores(path):
    """Load case_id -> score mapping from a judged file."""
    scores = {}
    if not path.exists():
        return scores
    with open(path) as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                scores[r.get("case_id", r.get("id", "?"))] = r.get("judge_score", 3)
    return scores


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--trace", required=True, help="Trace file to judge")
    p.add_argument("--corpus", required=True, help="Corpus file for case metadata")
    p.add_argument("--judge-model", required=True)
    p.add_argument(
        "--judge-backend", default="ollama", choices=["ollama", "openai", "anthropic"]
    )
    p.add_argument("--judge-url", default=None)
    p.add_argument("--output", required=True, help="Output JSONL path")
    p.add_argument(
        "--runs", type=int, default=3, help="Number of judge runs (default: 3)"
    )
    p.add_argument("--strict", action="store_true")
    args = p.parse_args()

    trace_path = Path(args.trace)
    output_path = Path(args.output)
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load trace to get case IDs
    with open(trace_path) as f:
        traces = [json.loads(l) for l in f if l.strip()]

    print(
        f"Probabilistic judging: {len(traces)} cases × {args.runs} runs = {len(traces) * args.runs} judge calls"
    )

    # Run judge N times
    all_run_scores = {}  # case_id -> [score_run1, score_run2, ...]
    for run_id in range(1, args.runs + 1):
        print(f"\n  Run {run_id}/{args.runs}...")
        run_output = run_judge_once(
            trace_path,
            args.corpus,
            args.judge_model,
            args.judge_backend,
            args.judge_url,
            output_dir,
            run_id,
            args.strict,
        )
        scores = load_scores(run_output)
        for cid, score in scores.items():
            if cid not in all_run_scores:
                all_run_scores[cid] = []
            all_run_scores[cid].append(score)

    # Compute median and agreement
    results = []
    agreements = []
    for r in traces:
        cid = r.get("case_id", r.get("id", "?"))
        scores = all_run_scores.get(cid, [3])
        median_score = statistics.median(scores)
        # Agreement: fraction of scores equal to the mode
        mode_score = (
            statistics.mode(scores) if len(set(scores)) < len(scores) else scores[0]
        )
        agreement = sum(1 for s in scores if s == mode_score) / len(scores)
        agreements.append(agreement)

        results.append(
            {
                **r,
                "judge_score": int(median_score),
                "judge_scores_all": scores,
                "judge_agreement": round(agreement, 2),
                "judge_model": args.judge_model,
            }
        )

    # Write output
    with open(output_path, "w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Summary
    avg_agreement = sum(agreements) / len(agreements) if agreements else 0
    print(
        f"\n  Average agreement: {avg_agreement:.2f} (1.0 = perfect, {1 / args.runs:.2f} = random)"
    )
    print(f"  Results: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
