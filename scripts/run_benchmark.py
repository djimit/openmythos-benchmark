#!/usr/bin/env python3
"""Run evaluate -> judge -> report -> optional regression gate."""

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent


def safe_name(value: str) -> str:
    return value.replace("/", "_").replace(":", "_").replace(" ", "_")


def run(cmd: list[str], dry_run: bool = False) -> None:
    print(shlex.join(cmd))
    if not dry_run:
        subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=REPO_ROOT / "cases" / "corpus.jsonl")
    parser.add_argument("--model")
    parser.add_argument("--backend", default="ollama", choices=["ollama", "openai", "anthropic"])
    parser.add_argument("--base-url")
    parser.add_argument("--api", default="chat", choices=["chat", "responses"])
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "traces" / "runs")
    parser.add_argument("--name")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--categories", nargs="+")
    parser.add_argument("--judge-model")
    parser.add_argument("--judge-backend", default="openai", choices=["ollama", "openai", "anthropic"])
    parser.add_argument("--judge-url")
    parser.add_argument("--judge-api", default="chat", choices=["chat", "responses"])
    parser.add_argument("--judge-reason", action="store_true", help="Ask judge.py to write judge_reason")
    parser.add_argument("--baseline", type=Path, help="Judged baseline JSONL for regression_gate.py")
    parser.add_argument("--min-delta", type=float, default=0.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--demo", action="store_true", help="Print a no-network example and exit")
    args = parser.parse_args()

    if args.demo:
        args.model = "llama3.1:8b"
        args.backend = "ollama"
        args.base_url = "http://192.168.1.28:11434"
        args.output_dir = Path("/tmp/openmythos-demo")
        args.categories = ["hierarchy"]
        args.limit = 1
        args.dry_run = True
    elif not args.model:
        parser.error("--model is required unless --demo is used")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    run_name = args.name or safe_name(args.model)
    raw_trace = args.output_dir / f"{run_name}.jsonl"
    judged_trace = args.output_dir / f"judged_{run_name}.jsonl"
    report_path = args.output_dir / f"{run_name}.md"

    evaluate = [
        sys.executable,
        str(SCRIPT_DIR / "evaluate.py"),
        "--corpus",
        str(args.corpus),
        "--model",
        args.model,
        "--backend",
        args.backend,
        "--api",
        args.api,
        "--output",
        str(raw_trace),
    ]
    if args.base_url:
        evaluate += ["--base-url", args.base_url]
    if args.limit:
        evaluate += ["--limit", str(args.limit)]
    if args.categories:
        evaluate += ["--categories", *args.categories]
    run(evaluate, args.dry_run)

    report_trace = raw_trace
    if args.judge_model:
        judge = [
            sys.executable,
            str(SCRIPT_DIR / "judge.py"),
            "--corpus",
            str(args.corpus),
            "--trace",
            str(raw_trace),
            "--judge-model",
            args.judge_model,
            "--judge-backend",
            args.judge_backend,
            "--judge-api",
            args.judge_api,
            "--output",
            str(judged_trace),
        ]
        if args.judge_url:
            judge += ["--judge-url", args.judge_url]
        if args.judge_reason:
            judge += ["--judge-reason"]
        run(judge, args.dry_run)
        report_trace = judged_trace

    run(
        [
            sys.executable,
            str(SCRIPT_DIR / "report.py"),
            "--trace",
            str(report_trace),
            "--output",
            str(report_path),
            "--title",
            f"{args.model} benchmark report",
        ],
        args.dry_run,
    )

    if args.baseline:
        if not args.judge_model:
            raise SystemExit("--baseline requires --judge-model because regression_gate.py needs judged traces")
        run(
            [
                sys.executable,
                str(SCRIPT_DIR / "regression_gate.py"),
                "--baseline",
                str(args.baseline),
                "--candidate",
                str(judged_trace),
                "--min-delta",
                str(args.min_delta),
            ],
            args.dry_run,
        )

    print(f"report: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
