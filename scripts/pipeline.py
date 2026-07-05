#!/usr/bin/env python3
"""OpenFable-to-Corpus pipeline — generate → evaluate → judge → discriminate → promote.

Chains the existing scripts into a closed loop that:
  1. Generates draft cases for weak categories (generate.py or generate_hard.py)
  2. Validates them against the corpus schema (validate_jsonl.py)
  3. Evaluates drafts against 2+ models (evaluate.py)
  4. Judges all traces with one consistent judge (judge.py)
  5. Measures discrimination — only cases that separate models survive (discrimination.py)
  6. Promotes survivors into corpus.jsonl, feeds failures to evolve.py for next iteration

Usage:
  python3 scripts/pipeline.py --demo
  python3 scripts/pipeline.py --categories value-alignment calibration --n 5 --hard --strict \
      --models "llama3.1:8b,qwen2.5:32b-instruct-q4_K_M" \
      --judge-model openai-gpt5 --judge-backend openai --judge-url "http://192.168.1.28:4000/v1" \
      --gen-backend openai --gen-base-url "http://192.168.1.28:4000/v1" --generate-model openai-gpt4o
"""

import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
CORPUS_PATH = REPO_ROOT / "cases" / "corpus.jsonl"

DEAD_CATEGORIES = ["value-alignment", "calibration", "hierarchy", "overthinking"]

KEEP_SPREAD_MIN = 1
KEEP_DEAD_RATE_MAX = 0.5
MAX_ITERATIONS = 3


def run(cmd, dry_run=False, env=None):
    print(f"  $ {shlex.join(cmd)}")
    if not dry_run:
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        result = subprocess.run(cmd, capture_output=True, text=True, env=merged_env)
        if result.stdout:
            print(result.stdout.rstrip())
        if result.returncode != 0:
            print(result.stderr.rstrip(), file=sys.stderr)
            raise SystemExit(
                f"command failed (exit {result.returncode}): {shlex.join(cmd)}"
            )


def verify_model(model, backend, base_url=None):
    """Check if a model is reachable. Returns (ok, error_msg)."""
    if backend == "ollama":
        url = f"{base_url or 'http://localhost:11434'}/api/generate"
        payload = json.dumps(
            {
                "model": model,
                "prompt": "hi",
                "stream": False,
                "options": {"num_predict": 1},
            }
        ).encode()
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )
    elif backend == "openai":
        url = f"{base_url or 'https://api.openai.com/v1'}/chat/completions"
        payload = json.dumps(
            {"model": model, "messages": [{"role": "user", "content": "hi"}]}
        ).encode()
        key = os.environ.get("OPENAI_API_KEY", "") or os.environ.get(
            "LITELLM_OPENCODE_KEY", ""
        )
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            },
        )
    else:
        return True, ""
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            json.loads(resp.read())
        return True, ""
    except Exception as e:
        return False, str(e)


def verify_models(models, backend, base_url, judge_model, judge_backend, judge_url):
    failures = []
    for model in models:
        ok, err = verify_model(model, backend, base_url)
        if not ok:
            failures.append(f"  evaluation model '{model}': {err}")
    ok, err = verify_model(judge_model, judge_backend, judge_url)
    if not ok:
        failures.append(f"  judge model '{judge_model}': {err}")
    return failures


def generate(
    category,
    n,
    model,
    output_dir,
    dry_run=False,
    gen_backend="openai",
    gen_base_url=None,
):
    out = output_dir / f"drafts_{category}.jsonl"
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "generate.py"),
        "--category",
        category,
        "--n",
        str(n),
        "--model",
        model,
        "--output",
        str(out),
        "--version",
        "1.1",
        "--backend",
        gen_backend,
    ]
    if gen_base_url:
        cmd += ["--base-url", gen_base_url]
    gen_env = {}
    if os.environ.get("OPENAI_API_KEY"):
        gen_env["OPENAI_API_KEY"] = os.environ["OPENAI_API_KEY"]
    if os.environ.get("LITELLM_OPENCODE_KEY"):
        gen_env["OPENAI_API_KEY"] = os.environ["LITELLM_OPENCODE_KEY"]
    run(cmd, dry_run, env=gen_env if gen_env else None)
    return out


def validate(draft_path, dry_run=False):
    cmd = [sys.executable, str(SCRIPT_DIR / "validate_jsonl.py"), str(draft_path)]
    print(f"  $ {shlex.join(cmd)}")
    if dry_run:
        return True
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  VALIDATION FAILED: {draft_path}")
        print(result.stdout.strip())
        return False
    print(f"  ✓ {result.stdout.strip()}")
    return True


def evaluate(draft_path, model, backend, base_url, output_dir, dry_run=False):
    safe = model.replace("/", "_").replace(":", "_")
    out = output_dir / f"{safe}.jsonl"
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "evaluate.py"),
        "--corpus",
        str(draft_path),
        "--model",
        model,
        "--backend",
        backend,
        "--output",
        str(out),
    ]
    if base_url:
        cmd += ["--base-url", base_url]
    run(cmd, dry_run)
    return out


def judge(
    trace_path,
    corpus_path,
    judge_model,
    judge_backend,
    judge_url,
    output_dir,
    dry_run=False,
    strict=False,
):
    safe = trace_path.stem
    out = output_dir / f"judged_{safe}.jsonl"
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
    run(cmd, dry_run)
    return out


def discriminate(judged_traces, dry_run=False):
    if len(judged_traces) < 2:
        raise ValueError("need at least 2 judged traces for discrimination")
    cmd = [sys.executable, str(SCRIPT_DIR / "discrimination.py")] + [
        str(p) for p in judged_traces
    ]
    print(f"  $ {shlex.join(cmd)}")
    if dry_run:
        return {"per_category": {}, "discrimination": 0, "dead_case_rate": 1.0}
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout.strip())
    if result.returncode != 0:
        print(result.stderr.rstrip(), file=sys.stderr)
    return _parse_discrimination_output(result.stdout)


def _parse_discrimination_output(text):
    report = {"per_category": {}, "discrimination": 0, "dead_case_rate": 1.0}
    for line in text.splitlines():
        if "discrimination (best - worst):" in line:
            report["discrimination"] = float(line.split(":")[1].strip().split()[0])
        elif "dead-case rate:" in line:
            report["dead_case_rate"] = float(line.split(":")[1].strip().split()[0])
        elif line.strip() and "=" in line and not line.startswith("─"):
            parts = line.strip().split()
            if len(parts) >= 4 and parts[0] not in ("cases", "per-model", "per"):
                cat = parts[0]
                try:
                    spread = float(parts[1].split("=")[1]) if "=" in parts[1] else 0
                    dead = float(parts[2].split("=")[1]) if "=" in parts[2] else 1
                    report["per_category"][cat] = {"spread": spread, "dead_rate": dead}
                except (ValueError, IndexError):
                    pass
    return report


def promote(draft_path, category, report, corpus_path, dry_run=False):
    cat_report = report["per_category"].get(category, {})
    spread = cat_report.get("spread", 0)
    dead_rate = cat_report.get("dead_rate", 1)

    if spread < KEEP_SPREAD_MIN:
        print(f"  ✗ {category}: spread={spread:.2f} < {KEEP_SPREAD_MIN} — SKIP")
        return 0, _count_jsonl(draft_path)
    if dead_rate > KEEP_DEAD_RATE_MAX:
        print(
            f"  ✗ {category}: dead_rate={dead_rate:.2f} > {KEEP_DEAD_RATE_MAX} — SKIP"
        )
        return 0, _count_jsonl(draft_path)

    count = 0
    if not dry_run and draft_path.exists():
        with open(draft_path) as f_in, open(corpus_path, "a") as f_out:
            for line in f_in:
                if line.strip():
                    case = json.loads(line)
                    case["validation_status"] = "reviewed"
                    f_out.write(json.dumps(case, ensure_ascii=False) + "\n")
                    count += 1
        print(
            f"  ✓ {category}: spread={spread:.2f}, dead={dead_rate:.2f} — PROMOTED {count}"
        )
    else:
        print(
            f"  ✓ {category}: spread={spread:.2f}, dead={dead_rate:.2f} — WOULD PROMOTE (dry_run={dry_run})"
        )
    return count, _count_jsonl(draft_path) - count


def _count_jsonl(path):
    if not path.exists():
        return 0
    return sum(1 for line in open(path) if line.strip())


def pipeline(args):
    start_time = time.time()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    categories = args.categories
    models = [m.strip() for m in args.models.split(",")]
    total_promoted = 0
    total_remaining = 0
    iteration_reports = []

    print(f"\n{'=' * 60}")
    print(f"OpenFable-to-Corpus Pipeline")
    print(f"  categories: {', '.join(categories)}")
    print(f"  models: {', '.join(models)}")
    print(f"  drafts per category: {args.n}")
    print(f"  judge: {args.judge_model} ({args.judge_backend})")
    print(f"  max iterations: {args.max_iterations}")
    print(f"{'=' * 60}\n")

    print("Preflight: verifying model availability...")
    failures = verify_models(
        models,
        args.backend,
        args.base_url,
        args.judge_model,
        args.judge_backend,
        args.judge_url,
    )
    if failures:
        print("\n✗ Model verification failed:")
        for f in failures:
            print(f)
        print(
            "\nFix model names or check endpoint. Local: llama3.1:8b, qwen2.5:32b-instruct-q4_K_M"
        )
        print("LiteLLM: openai-gpt4o, openai-gpt5, deepseek-chat")
        raise SystemExit("pipeline aborted: model verification failed")
    print("  ✓ all models reachable\n")

    for iteration in range(1, args.max_iterations + 1):
        print(f"\n--- Iteration {iteration}/{args.max_iterations} ---\n")
        iteration_promoted = 0

        for category in categories:
            print(f"\n[{category}]")

            # Stage 1: Generate
            print(
                f"\n  [1/5] Generating {args.n} draft cases {'(HARD)' if args.hard else ''}..."
            )
            if args.hard:
                out = output_dir / f"hard_drafts_{category}.jsonl"
                cmd = [
                    sys.executable,
                    str(SCRIPT_DIR / "generate_hard.py"),
                    "--category",
                    category,
                    "--n",
                    str(args.n),
                    "--difficulty",
                    str(args.min_difficulty),
                    "--model",
                    args.generate_model,
                    "--backend",
                    args.gen_backend,
                    "--base-url",
                    args.gen_base_url,
                    "--output",
                    str(out),
                    "--version",
                    "1.1",
                ]
                gen_env = {}
                if os.environ.get("OPENAI_API_KEY"):
                    gen_env["OPENAI_API_KEY"] = os.environ["OPENAI_API_KEY"]
                if os.environ.get("LITELLM_OPENCODE_KEY"):
                    gen_env["OPENAI_API_KEY"] = os.environ["LITELLM_OPENCODE_KEY"]
                run(cmd, args.dry_run, env=gen_env if gen_env else None)
                draft_path = out
            else:
                draft_path = generate(
                    category,
                    args.n,
                    args.generate_model,
                    output_dir,
                    args.dry_run,
                    gen_backend=args.gen_backend,
                    gen_base_url=args.gen_base_url,
                )

            # Stage 2: Validate
            print(f"\n  [2/5] Validating schema...")
            if not validate(draft_path, args.dry_run):
                continue

            # Stage 3: Evaluate
            print(f"\n  [3/5] Evaluating against {len(models)} models...")
            traces = []
            for model in models:
                trace = evaluate(
                    draft_path,
                    model,
                    args.backend,
                    args.base_url,
                    output_dir,
                    args.dry_run,
                )
                traces.append(trace)

            # Stage 4: Judge (use draft_path as corpus for new case IDs)
            print(f"\n  [4/5] Judging {len(traces)} traces...")
            judged_traces = []
            for trace in traces:
                jt = judge(
                    trace,
                    draft_path,
                    args.judge_model,
                    args.judge_backend,
                    args.judge_url,
                    output_dir,
                    args.dry_run,
                    strict=args.strict,
                )
                judged_traces.append(jt)

            # Stage 5: Discriminate
            print(f"\n  [5/5] Measuring discrimination...")
            report = discriminate(judged_traces, args.dry_run)

            promoted, remaining = promote(
                draft_path, category, report, CORPUS_PATH, args.dry_run
            )
            iteration_promoted += promoted
            total_promoted += promoted
            total_remaining += remaining

        iteration_reports.append(
            {"iteration": iteration, "promoted": iteration_promoted}
        )
        if iteration_promoted == 0:
            print(f"\nNo cases promoted in iteration {iteration}. Stopping.")
            break

    elapsed = time.time() - start_time
    report_path = output_dir / "pipeline_report.md"
    _write_report(
        report_path,
        categories,
        models,
        args,
        total_promoted,
        total_remaining,
        iteration_reports,
        elapsed,
    )

    print(f"\n{'=' * 60}")
    print(f"Pipeline complete: {total_promoted} promoted, {total_remaining} remaining")
    print(f"  report: {report_path}")
    print(f"  elapsed: {elapsed:.1f}s")
    print(f"{'=' * 60}\n")
    return 0


def _write_report(
    path, categories, models, args, promoted, remaining, iterations, elapsed
):
    lines = [
        "# OpenFable-to-Corpus Pipeline Report",
        "",
        f"- **Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **Categories**: {', '.join(categories)}",
        f"- **Models**: {', '.join(models)}",
        f"- **Drafts per category**: {args.n}",
        f"- **Judge**: {args.judge_model} ({args.judge_backend})",
        f"- **Iterations**: {len(iterations)}",
        f"- **Hard mode**: {args.hard}",
        f"- **Strict**: {args.strict}",
        "",
        "## Results",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Cases promoted | {promoted} |",
        f"| Cases remaining | {remaining} |",
        f"| Elapsed | {elapsed:.1f}s |",
        "",
        "## Iterations",
        "",
        "| Iteration | Promoted |",
        "|-----------|----------|",
    ]
    for it in iterations:
        lines.append(f"| {it['iteration']} | {it['promoted']} |")
    lines.extend(["", "## Next Steps", ""])
    if remaining > 0:
        lines.append(
            f"- {remaining} drafts remain — review manually or re-run with higher difficulty."
        )
    if promoted > 0:
        lines.append(f"- {promoted} cases promoted to corpus.jsonl.")
        lines.append("- Run discrimination.py on full corpus to verify improvement.")
    lines.append("")
    path.write_text("\n".join(lines))
    print(f"\n{'─' * 40}\n{''.join(lines)}\n{'─' * 40}")


def _demo():
    print("Pipeline demo mode — verifying structure...\n")
    scripts = [
        "generate.py",
        "generate_hard.py",
        "validate_jsonl.py",
        "evaluate.py",
        "judge.py",
        "discrimination.py",
        "evolve.py",
    ]
    for s in scripts:
        p = SCRIPT_DIR / s
        assert p.exists(), f"missing script: {p}"
        print(f"  ✓ {s}")
    assert CORPUS_PATH.exists(), f"missing corpus: {CORPUS_PATH}"
    print(f"  ✓ corpus.jsonl ({_count_jsonl(CORPUS_PATH)} cases)")
    print("\ndemo OK: all scripts present")
    return 0


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--categories",
        nargs="+",
        default=DEAD_CATEGORIES,
        help=f"Categories (default: {' '.join(DEAD_CATEGORIES)})",
    )
    p.add_argument("--n", type=int, default=5, help="Drafts per category (default: 5)")
    p.add_argument(
        "--models",
        default="llama3.1:8b,qwen2.5:32b-instruct-q4_K_M",
        help="Comma-separated models (default: llama3.1:8b,qwen2.5:32b-instruct-q4_K_M)",
    )
    p.add_argument(
        "--backend", default="ollama", choices=["ollama", "openai", "anthropic"]
    )
    p.add_argument(
        "--base-url", default="http://192.168.1.28:11434", help="API base URL"
    )
    p.add_argument(
        "--judge-model",
        default="openai-gpt5",
        help="Judge model (default: openai-gpt5)",
    )
    p.add_argument(
        "--judge-backend", default="openai", choices=["ollama", "openai", "anthropic"]
    )
    p.add_argument(
        "--judge-url", default="http://192.168.1.28:4000/v1", help="Judge API URL"
    )
    p.add_argument("--strict", action="store_true", help="Use stricter scoring rubric")
    p.add_argument("--generate-model", default="openai-gpt4o", help="Generation model")
    p.add_argument("--gen-backend", default="openai", choices=["anthropic", "openai"])
    p.add_argument(
        "--gen-base-url", default="http://192.168.1.28:4000/v1", help="Gen API URL"
    )
    p.add_argument(
        "--hard", action="store_true", help="Use generate_hard.py for adversarial cases"
    )
    p.add_argument(
        "--min-difficulty", type=int, default=4, help="Min difficulty (default: 4)"
    )
    p.add_argument("--output-dir", type=Path, default=REPO_ROOT / "traces" / "pipeline")
    p.add_argument("--max-iterations", type=int, default=MAX_ITERATIONS)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--demo", action="store_true")

    args = p.parse_args()
    if args.demo:
        return _demo()
    if len(args.models.split(",")) < 2:
        p.error("need at least 2 models for discrimination")
    return pipeline(args)


if __name__ == "__main__":
    sys.exit(main())
