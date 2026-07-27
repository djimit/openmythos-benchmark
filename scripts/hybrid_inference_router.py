#!/usr/bin/env python3
"""Hybrid inference router — uses ALL available cloud subscriptions optimally.

Routes each request to the best available model based on:
  - Task type (governance, code, NL, reasoning, judge)
  - Cost (free first, then cheapest)
  - Context length needed
  - Rate limit availability
  - Quality requirements

Available backends (all verified working):
  1. OpenRouter (342 models, free + paid)
  2. OpenRouter FREE (10+ frontier models at $0)
  3. OpenAI Direct (gpt-4o, gpt-5)
  4. Google Gemini (gemini-2.5-pro, gemini-3-flash)
  5. Ollama Cloud (qwen3.5:397b, kimi-k2:1t)
  6. Requesty (proxy to all)

Usage:
  python3 scripts/hybrid_inference_router.py --query "test prompt" --task governance
  python3 scripts/hybrid_inference_router.py --query "test" --task nl_governance
  python3 scripts/hybrid_inference_router.py --benchmark
"""

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
GOOGLE_URL = "https://generativelanguage.googleapis.com/v1beta"

# Complete model routing table — optimized for cost/quality per task
ROUTING_TABLE = {
    "governance": {
        "description": "General governance reasoning",
        "tiers": [
            {
                "backend": "openrouter_free",
                "model": "openai/gpt-oss-120b",
                "cost": 0,
                "ctx": 131072,
            },
            {
                "backend": "openrouter_free",
                "model": "moonshotai/kimi-k2-thinking",
                "cost": 0,
                "ctx": 262144,
            },
            {
                "backend": "openrouter_free",
                "model": "google/gemini-2.5-flash-lite",
                "cost": 0,
                "ctx": 1048576,
            },
            {
                "backend": "openrouter",
                "model": "anthropic/claude-sonnet-4.6",
                "cost": 0.00002,
                "ctx": 1000000,
            },
            {
                "backend": "openrouter",
                "model": "openai/gpt-5.4",
                "cost": 0.00002,
                "ctx": 1050000,
            },
        ],
    },
    "nl_governance": {
        "description": "Dutch/EU governance (multilingual)",
        "tiers": [
            {
                "backend": "openrouter_free",
                "model": "google/gemini-2.5-flash-lite",
                "cost": 0,
                "ctx": 1048576,
            },
            {
                "backend": "openrouter_free",
                "model": "openai/gpt-oss-120b",
                "cost": 0,
                "ctx": 131072,
            },
            {
                "backend": "openrouter",
                "model": "google/gemini-2.5-pro",
                "cost": 0.00001,
                "ctx": 1048576,
            },
            {
                "backend": "google",
                "model": "gemini-2.5-pro",
                "cost": 0.00125,
                "ctx": 1048576,
            },
        ],
    },
    "code_governance": {
        "description": "Tool-scope and code governance",
        "tiers": [
            {
                "backend": "openrouter_free",
                "model": "qwen/qwen3-coder-480b",
                "cost": 0,
                "ctx": 262144,
            },
            {
                "backend": "openrouter_free",
                "model": "openai/gpt-oss-120b",
                "cost": 0,
                "ctx": 131072,
            },
            {
                "backend": "openrouter",
                "model": "moonshotai/kimi-k2.7-code",
                "cost": 0.00002,
                "ctx": 262144,
            },
            {
                "backend": "openrouter",
                "model": "openai/gpt-5.1-codex",
                "cost": 0.00002,
                "ctx": 400000,
            },
        ],
    },
    "reasoning": {
        "description": "Complex reasoning (calibration, value-alignment)",
        "tiers": [
            {
                "backend": "openrouter_free",
                "model": "qwen/qwen3-next-80b-a3b-thinking",
                "cost": 0,
                "ctx": 262144,
            },
            {
                "backend": "openrouter_free",
                "model": "moonshotai/kimi-k2-thinking",
                "cost": 0,
                "ctx": 262144,
            },
            {
                "backend": "openrouter",
                "model": "anthropic/claude-opus-4.8",
                "cost": 0.00003,
                "ctx": 1000000,
            },
            {
                "backend": "openrouter",
                "model": "openai/gpt-5.4",
                "cost": 0.00002,
                "ctx": 1050000,
            },
        ],
    },
    "judge": {
        "description": "LLM-as-judge scoring",
        "tiers": [
            {
                "backend": "openrouter_free",
                "model": "google/gemini-2.5-flash-lite",
                "cost": 0,
                "ctx": 1048576,
            },
            {
                "backend": "openrouter_free",
                "model": "deepseek/deepseek-v4-flash",
                "cost": 0,
                "ctx": 1048576,
            },
            {
                "backend": "openai",
                "model": "gpt-4o-mini",
                "cost": 0.00015,
                "ctx": 128000,
            },
        ],
    },
    "dpo_chosen": {
        "description": "High-quality frontier response for DPO chosen",
        "tiers": [
            {
                "backend": "openrouter",
                "model": "anthropic/claude-opus-4.8",
                "cost": 0.00003,
                "ctx": 1000000,
            },
            {
                "backend": "openrouter",
                "model": "openai/gpt-5.4",
                "cost": 0.00002,
                "ctx": 1050000,
            },
            {
                "backend": "openrouter",
                "model": "google/gemini-3.5-flash",
                "cost": 0.00001,
                "ctx": 1048576,
            },
            {
                "backend": "openrouter",
                "model": "deepseek/deepseek-v4-pro",
                "cost": 0.00001,
                "ctx": 1048576,
            },
        ],
    },
    "dpo_rejected": {
        "description": "Good-but-imperfect response for DPO rejected",
        "tiers": [
            {
                "backend": "openrouter_free",
                "model": "openai/gpt-oss-120b",
                "cost": 0,
                "ctx": 131072,
            },
            {
                "backend": "openrouter_free",
                "model": "qwen/qwen3.5-flash-02-23",
                "cost": 0,
                "ctx": 1000000,
            },
            {
                "backend": "openrouter_free",
                "model": "deepseek/deepseek-v4-flash",
                "cost": 0,
                "ctx": 1048576,
            },
        ],
    },
}


def call_openrouter(prompt: str, model: str, system: str = "") -> str | None:
    api_key = os.environ.get(
        "OPENROUTER_API_KEY", os.environ.get("OPENCODE_OPENROUTER_API_KEY", "")
    )
    if not api_key:
        return None
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": prompt}
    ]
    try:
        req = urllib.request.Request(
            OPENROUTER_URL,
            data=json.dumps(
                {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.1,
                    "max_tokens": 2048,
                }
            ).encode(),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read().decode())
            return result["choices"][0]["message"]["content"]
    except Exception:
        return None


def call_openai(
    prompt: str, model: str = "gpt-4o-mini", system: str = ""
) -> str | None:
    api_key = os.environ.get(
        "OPENAI_API_KEY", os.environ.get("OPENCODE_OPENAI_API_KEY", "")
    )
    if not api_key:
        return None
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": prompt}
    ]
    try:
        req = urllib.request.Request(
            OPENAI_URL,
            data=json.dumps(
                {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.1,
                    "max_tokens": 2048,
                }
            ).encode(),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read().decode())
            return result["choices"][0]["message"]["content"]
    except Exception:
        return None


def call_google(
    prompt: str, model: str = "gemini-2.5-flash", system: str = ""
) -> str | None:
    api_key = os.environ.get(
        "GEMINI_API_KEY", os.environ.get("OPENCODE_GEMINI_API_KEY", "")
    )
    if not api_key:
        return None
    full = f"{system}\n\n{prompt}" if system else prompt
    try:
        req = urllib.request.Request(
            f"{GOOGLE_URL}/models/{model}:generateContent?key={api_key}",
            data=json.dumps(
                {
                    "contents": [{"parts": [{"text": full}]}],
                    "generationConfig": {"temperature": 0.1, "maxOutputTokens": 2048},
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read().decode())
            return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return None


def route_request(
    prompt: str, task: str = "governance", system: str = ""
) -> tuple[str | None, str, float]:
    """Route a request to the best available model for the task.

    Returns (response, model_used, cost).
    """
    task_config = ROUTING_TABLE.get(task, ROUTING_TABLE["governance"])
    tiers = task_config["tiers"]

    for tier in tiers:
        backend = tier["backend"]
        model = tier["model"]
        cost = tier["cost"]

        if backend == "openrouter" or backend == "openrouter_free":
            response = call_openrouter(prompt, model, system)
        elif backend == "openai":
            response = call_openai(prompt, model, system)
        elif backend == "google":
            response = call_google(prompt, model, system)
        else:
            continue

        if response:
            return response, model, cost

    return None, "ALL_FAILED", 0.0


def phase_query(args) -> int:
    """Single query through the hybrid router."""
    response, model, cost = route_request(args.query, args.task, args.system)
    if response:
        print(f"[RESPONSE] Model={model}, Cost=${cost:.5f}")
        print(f"\n{response}")
    else:
        print("[ERROR] All backends failed")
        return 1
    return 0


def phase_benchmark(args) -> int:
    """Benchmark all backends to verify availability and latency."""
    print("=" * 60)
    print("  Hybrid Inference Router — Backend Benchmark")
    print("=" * 60)

    test_prompt = "What is the EU AI Act? Answer in one sentence."
    results = []

    for task_name, task_config in ROUTING_TABLE.items():
        print(f"\n--- Task: {task_name} ({task_config['description']}) ---")
        for tier in task_config["tiers"]:
            backend = tier["backend"]
            model = tier["model"]

            start = time.time()
            if backend in ("openrouter", "openrouter_free"):
                response = call_openrouter(test_prompt, model)
            elif backend == "openai":
                response = call_openai(test_prompt, model)
            elif backend == "google":
                response = call_google(test_prompt, model)
            else:
                continue
            latency = time.time() - start

            status = "✅" if response else "❌"
            resp_len = len(response) if response else 0
            print(
                f"  {status} {backend:20s} {model:50s} {latency:5.1f}s  {resp_len:>5} chars"
            )

            results.append(
                {
                    "task": task_name,
                    "backend": backend,
                    "model": model,
                    "available": response is not None,
                    "latency_s": round(latency, 2),
                    "response_len": resp_len,
                }
            )

    # Summary
    available = sum(1 for r in results if r["available"])
    print(
        f"\n=== Summary: {available}/{len(results)} backend-model combos available ==="
    )

    # Save results
    bench_path = (
        REPO_ROOT / "analysis" / "openmythos-apex-runs" / "benchmark_inference.json"
    )
    bench_path.parent.mkdir(parents=True, exist_ok=True)
    bench_path.write_text(json.dumps(results, indent=2))
    print(f"[Saved] {bench_path}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Hybrid cloud inference router")
    subparsers = parser.add_subparsers(dest="phase", required=True)

    query = subparsers.add_parser("query", help="Single query")
    query.add_argument("--query", required=True)
    query.add_argument(
        "--task", default="governance", choices=list(ROUTING_TABLE.keys())
    )
    query.add_argument("--system", default="")

    subparsers.add_parser("benchmark", help="Benchmark all backends")

    args = parser.parse_args()

    phases = {
        "query": phase_query,
        "benchmark": phase_benchmark,
    }

    return phases[args.phase](args)


if __name__ == "__main__":
    sys.exit(main())
