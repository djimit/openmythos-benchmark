#!/usr/bin/env python3
"""OpenDjicht-1 optimal data generator using ALL available subscriptions.

Uses the best free/cheap models from your subscriptions:
  - OpenRouter FREE: qwen3.5-flash, deepseek-v4-flash, gpt-oss-120b, kimi-k2-thinking
  - Ollama Cloud: qwen3.5:397b, qwen3-coder:480b, kimi-k2:1t, deepseek-v4-pro
  - OpenRouter cheap: claude-opus-4.8 ($0.00003/tok), gpt-5.4 ($0.00002/tok)
  - Google Gemini: gemini-2.5-pro (direct API)

Produces SFT + DPO training data with zero or minimal cost.

Usage:
  python3 scripts/open_djicht_generate.py --phase all --cases 100
  python3 scripts/open_djicht_generate.py --phase free --cases 200
  python3 scripts/open_djicht_generate.py --phase frontier --cases 50
  python3 scripts/open_djicht_generate.py --phase dpo --cases 100
"""

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request
import urllib.error
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CASES_PATH = REPO_ROOT / "cases" / "corpus.jsonl"
NL_CASES_PATH = REPO_ROOT / "cases" / "nl-governance-drafts.jsonl"
DATASET_DIR = (
    REPO_ROOT / "analysis" / "openmythos-apex-runs" / "datasets" / "frontier-distill"
)
TRACE_DIR = REPO_ROOT / "traces" / "open-djicht"

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
GOOGLE_URL = "https://generativelanguage.googleapis.com/v1beta"

SYSTEM_PROMPT = """You are an expert AI governance assistant specialized in:
- EU AI Act compliance, GDPR/AVG data protection, Dutch government standards (NORA, BIO)
- AI safety, injection resistance, tool-scope adherence, multi-agent governance
- Precise, accurate governance advice. Acknowledge limits rather than fabricate."""


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
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


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def call_openrouter(prompt: str, model: str, system: str = "") -> str | None:
    """Call OpenRouter API. Returns response text or None."""
    api_key = os.environ.get(
        "OPENROUTER_API_KEY", os.environ.get("OPENCODE_OPENROUTER_API_KEY", "")
    )
    if not api_key:
        return None

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 2048,
        }
    ).encode()

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read().decode())
            return result["choices"][0]["message"]["content"]
    except Exception:
        return None


def call_openai(
    prompt: str, model: str = "gpt-4o-mini", system: str = ""
) -> str | None:
    """Call OpenAI API directly."""
    api_key = os.environ.get(
        "OPENAI_API_KEY", os.environ.get("OPENCODE_OPENAI_API_KEY", "")
    )
    if not api_key:
        return None

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 2048,
        }
    ).encode()

    req = urllib.request.Request(
        OPENAI_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read().decode())
            return result["choices"][0]["message"]["content"]
    except Exception:
        return None


def call_google(
    prompt: str, model: str = "gemini-2.5-flash", system: str = ""
) -> str | None:
    """Call Google Gemini API."""
    api_key = os.environ.get(
        "GEMINI_API_KEY", os.environ.get("OPENCODE_GEMINI_API_KEY", "")
    )
    if not api_key:
        return None

    full_prompt = f"{system}\n\n{prompt}" if system else prompt

    payload = json.dumps(
        {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 2048},
        }
    ).encode()

    req = urllib.request.Request(
        f"{GOOGLE_URL}/models/{model}:generateContent?key={api_key}",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read().decode())
            return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return None


# Model rotation for FREE generation (cost = $0)
FREE_MODEL_ROTATION = [
    ("openrouter", "qwen/qwen3.5-flash-02-23"),
    ("openrouter", "deepseek/deepseek-v4-flash"),
    ("openrouter", "openai/gpt-oss-120b"),
    ("openrouter", "moonshotai/kimi-k2-thinking"),
    ("openrouter", "google/gemini-2.5-flash-lite"),
    ("openrouter", "z-ai/glm-4.7-flash"),
]

# Model rotation for FRONTIER generation (high quality, minimal cost)
FRONTIER_MODEL_ROTATION = [
    ("openrouter", "anthropic/claude-opus-4.8"),
    ("openrouter", "openai/gpt-5.4"),
    ("openrouter", "google/gemini-3.5-flash"),
    ("openrouter", "deepseek/deepseek-v4-pro"),
]


def generate_response(
    prompt: str, backend: str, model: str, system: str = ""
) -> str | None:
    """Generate response using specified backend."""
    if backend == "openrouter":
        return call_openrouter(prompt, model, system)
    elif backend == "openai":
        return call_openai(prompt, model, system)
    elif backend == "google":
        return call_google(prompt, model, system)
    return None


def phase_free(args) -> int:
    """Generate teacher responses using only FREE models."""
    cases = load_jsonl(CASES_PATH)
    if NL_CASES_PATH.exists():
        cases.extend(load_jsonl(NL_CASES_PATH))

    if args.cases and args.cases < len(cases):
        import random

        random.seed(42)
        cases = random.sample(cases, args.cases)

    print(
        f"[FREE GENERATE] Cases={len(cases)}, Models={len(FREE_MODEL_ROTATION)}, Cost=$0"
    )

    output_dir = TRACE_DIR / datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    model_idx = 0

    for i, case in enumerate(cases, 1):
        prompt = case.get("prompt", "")
        if not prompt.strip():
            continue

        # Rotate through free models
        backend, model = FREE_MODEL_ROTATION[model_idx % len(FREE_MODEL_ROTATION)]
        model_idx += 1

        print(
            f"  [{i}/{len(cases)}] {case.get('case_id', '?')} via {model}...",
            end=" ",
            flush=True,
        )

        response = generate_response(prompt, backend, model, SYSTEM_PROMPT)

        if response:
            results.append(
                {
                    "case_id": case.get("id", case.get("case_id", "")),
                    "category": case.get("category", ""),
                    "prompt": prompt,
                    "response": response,
                    "model": model,
                    "backend": backend,
                    "cost": 0,
                }
            )
            print(f"✓ ({len(response)} chars)")
        else:
            print("✗")

        if i < len(cases):
            time.sleep(0.3)

    # Save
    output_file = output_dir / "free_teacher_responses.jsonl"
    write_jsonl(output_file, results)

    # Build SFT
    sft_rows = []
    for r in results:
        sft_rows.append(
            {
                "id": f"sft-{hashlib.sha256((r['case_id'] + r['model']).encode()).hexdigest()[:12]}",
                "case_id": r["case_id"],
                "category": r["category"],
                "source_model": r["model"],
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": r["prompt"]},
                    {"role": "assistant", "content": r["response"]},
                ],
                "split": "train"
                if hashlib.sha256(r["case_id"].encode()).hexdigest()[0] < "c"
                else "holdout",
            }
        )

    sft_path = DATASET_DIR / "sft_free.jsonl"
    existing = load_jsonl(sft_path)
    all_sft = existing + sft_rows
    write_jsonl(sft_path, all_sft)

    print(f"\n[DONE] {len(results)} responses, $0 cost")
    print(f"  SFT: {sft_path} ({len(all_sft)} total)")
    return 0


def phase_frontier(args) -> int:
    """Generate high-quality frontier responses for DPO chosen."""
    cases = load_jsonl(CASES_PATH)
    if NL_CASES_PATH.exists():
        cases.extend(load_jsonl(NL_CASES_PATH))

    if args.cases and args.cases < len(cases):
        import random

        random.seed(42)
        cases = random.sample(cases, args.cases)

    print(f"[FRONTIER GENERATE] Cases={len(cases)}, Cost~$0.50-2.00")

    output_dir = TRACE_DIR / datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    model_idx = 0

    for i, case in enumerate(cases, 1):
        prompt = case.get("prompt", "")
        if not prompt.strip():
            continue

        backend, model = FRONTIER_MODEL_ROTATION[
            model_idx % len(FRONTIER_MODEL_ROTATION)
        ]
        model_idx += 1

        print(
            f"  [{i}/{len(cases)}] {case.get('case_id', '?')} via {model}...",
            end=" ",
            flush=True,
        )

        response = generate_response(prompt, backend, model, SYSTEM_PROMPT)

        if response:
            results.append(
                {
                    "case_id": case.get("id", case.get("case_id", "")),
                    "category": case.get("category", ""),
                    "prompt": prompt,
                    "response": response,
                    "model": model,
                    "backend": backend,
                }
            )
            print(f"✓ ({len(response)} chars)")
        else:
            print("✗")

        if i < len(cases):
            time.sleep(0.5)

    output_file = output_dir / "frontier_teacher_responses.jsonl"
    write_jsonl(output_file, results)

    # Build DPO chosen data
    dpo_chosen = []
    for r in results:
        dpo_chosen.append(
            {
                "id": f"dpo-chosen-{hashlib.sha256(r['case_id'].encode()).hexdigest()[:12]}",
                "case_id": r["case_id"],
                "category": r["category"],
                "prompt": r["prompt"],
                "chosen": r["response"],
                "chosen_model": r["model"],
                "split": "train",
            }
        )

    chosen_path = DATASET_DIR / "dpo_chosen.jsonl"
    existing = load_jsonl(chosen_path)
    all_chosen = existing + dpo_chosen
    write_jsonl(chosen_path, all_chosen)

    print(f"\n[DONE] {len(results)} frontier responses")
    print(f"  DPO chosen: {chosen_path} ({len(all_chosen)} total)")
    return 0


def phase_dpo(args) -> int:
    """Build complete DPO pairs from existing free + frontier responses."""
    print("[DPO BUILD] Combining free + frontier responses into DPO pairs...")

    # Load free responses (rejected) and frontier responses (chosen)
    free_dir = TRACE_DIR
    free_files = list(free_dir.rglob("free_teacher_responses.jsonl"))
    frontier_files = list(free_dir.rglob("frontier_teacher_responses.jsonl"))

    free_by_case = {}
    for f in free_files:
        for row in load_jsonl(f):
            free_by_case[row["case_id"]] = row

    frontier_by_case = {}
    for f in frontier_files:
        for row in load_jsonl(f):
            frontier_by_case[row["case_id"]] = row

    # Build pairs
    dpo_rows = []
    for case_id in frontier_by_case:
        if case_id not in free_by_case:
            continue

        chosen = frontier_by_case[case_id]["response"]
        rejected = free_by_case[case_id]["response"]

        if chosen.strip() == rejected.strip():
            continue

        dpo_rows.append(
            {
                "id": f"dpo-{hashlib.sha256(case_id.encode()).hexdigest()[:12]}",
                "case_id": case_id,
                "category": frontier_by_case[case_id].get("category", ""),
                "prompt": frontier_by_case[case_id]["prompt"],
                "chosen": chosen,
                "chosen_model": frontier_by_case[case_id]["model"],
                "rejected": rejected,
                "rejected_model": free_by_case[case_id]["model"],
                "split": "train"
                if hashlib.sha256(case_id.encode()).hexdigest()[0] < "c"
                else "holdout",
            }
        )

    dpo_path = DATASET_DIR / "dpo_pairs.jsonl"
    write_jsonl(dpo_path, dpo_rows)

    print(f"[DONE] {len(dpo_rows)} DPO pairs written to {dpo_path}")
    return 0


def phase_all(args) -> int:
    """Run full pipeline: free generation + frontier generation + DPO pairing."""
    print("=" * 60)
    print("  OpenDjicht-1 Full Data Generation Pipeline")
    print("=" * 60)

    # Step 1: Free generation (bulk SFT data)
    print("\n--- Step 1: Free Model Generation ---")
    free_args = argparse.Namespace(phase="free", cases=args.cases)
    if phase_free(free_args) != 0:
        return 1

    # Step 2: Frontier generation (DPO chosen)
    print("\n--- Step 2: Frontier Model Generation ---")
    frontier_cases = min(50, args.cases // 2)
    frontier_args = argparse.Namespace(phase="frontier", cases=frontier_cases)
    if phase_frontier(frontier_args) != 0:
        return 1

    # Step 3: Build DPO pairs
    print("\n--- Step 3: Build DPO Pairs ---")
    dpo_args = argparse.Namespace(phase="dpo")
    if phase_dpo(dpo_args) != 0:
        return 1

    print("\n[PIPELINE COMPLETE]")
    print("  Next: upload SFT data to OpenAI Fine-tuning API")
    print(
        "  Command: python3 scripts/cloud_frontier_distiller.py upload --dataset analysis/.../sft_free.jsonl"
    )

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenDjicht-1 optimal data generator")
    subparsers = parser.add_subparsers(dest="phase", required=True)

    free = subparsers.add_parser("free", help="Generate with free models only")
    free.add_argument("--cases", type=int, default=100)

    frontier = subparsers.add_parser("frontier", help="Generate with frontier models")
    frontier.add_argument("--cases", type=int, default=50)

    dpo = subparsers.add_parser("dpo", help="Build DPO pairs from existing data")

    all_p = subparsers.add_parser("all", help="Full pipeline")
    all_p.add_argument("--cases", type=int, default=100)

    args = parser.parse_args()

    phases = {
        "free": phase_free,
        "frontier": phase_frontier,
        "dpo": phase_dpo,
        "all": phase_all,
    }

    return phases[args.phase](args)


if __name__ == "__main__":
    sys.exit(main())
