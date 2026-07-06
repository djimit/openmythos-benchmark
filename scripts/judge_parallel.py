#!/usr/bin/env python3
"""Judge multiple trace files sequentially but efficiently.

Usage:
  python3 scripts/judge_parallel.py --input-dir traces/per_cat/ --pattern "eval_qwen14b_*.jsonl" \
      --corpus-dir traces/per_cat/ --judge-model openai-gpt5 --judge-url "http://192.168.1.28:4000/v1" \
      --output-dir traces/per_cat/ --strict
"""

import argparse
import json
import os
import subprocess
import sys
import glob
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", required=True)
    p.add_argument("--pattern", required=True)
    p.add_argument("--corpus-dir", required=True)
    p.add_argument("--judge-model", required=True)
    p.add_argument("--judge-backend", default="ollama")
    p.add_argument("--judge-url", default=None)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--strict", action="store_true")
    args = p.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    trace_files = sorted(glob.glob(str(input_dir / args.pattern)))
    print(f"Found {len(trace_files)} trace files to judge")

    for i, trace_path in enumerate(trace_files):
        trace_path = Path(trace_path)
        # Derive corpus path: eval_qwen14b_calibration.jsonl -> calibration.jsonl
        cat_name = trace_path.stem.replace("eval_qwen14b_", "").replace("eval_", "")
        corpus_path = Path(args.corpus_dir) / f"{cat_name}.jsonl"
        output_path = (
            output_dir / f"judged_{trace_path.stem.replace('eval_', '')}.jsonl"
        )

        if not corpus_path.exists():
            print(f"  [{i + 1}/{len(trace_files)}] SKIP {trace_path.name} (no corpus)")
            continue

        print(f"  [{i + 1}/{len(trace_files)}] Judging {trace_path.name}...")
        cmd = [
            sys.executable,
            str(SCRIPT_DIR / "judge.py"),
            "--trace",
            str(trace_path),
            "--corpus",
            str(corpus_path),
            "--judge-model",
            args.judge_model,
            "--judge-backend",
            args.judge_backend,
            "--output",
            str(output_path),
        ]
        if args.judge_url:
            cmd += ["--judge-url", args.judge_url]
        if args.strict:
            cmd.append("--strict")

        import os

        env = os.environ.copy()
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        for line in result.stdout.splitlines():
            if "Average" in line:
                print(f"    {line.strip()}")

    print(f"\nDone. Results in {output_dir}")


if __name__ == "__main__":
    sys.exit(main())
