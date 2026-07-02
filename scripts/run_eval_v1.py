#!/usr/bin/env python3
"""Run 33-case subset against multiple models on workstation via Ollama."""

import json
import time
import urllib.request
import sys
from pathlib import Path

CORPUS_PATH = Path("/mnt/data/openmythos/openmythos-benchmark/cases/corpus_18.jsonl")
OUTPUT_DIR = Path("/mnt/data/openmythos/openmythos-benchmark/traces")
OLLAMA_URL = "http://localhost:11434"

MODELS = [
    "llama3.1:8b",
    "qwen2.5-coder:7b",
    "ornith-1.0-9b",
]


def load_cases():
    cases = []
    with open(CORPUS_PATH) as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))
    return cases


def call_ollama(prompt, model):
    url = f"{OLLAMA_URL}/api/generate"
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0, "num_predict": 256},
        }
    ).encode()
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read())
        elapsed = time.time() - start
        return {
            "response": result.get("response", ""),
            "tokens": result.get("eval_count", 0),
            "latency_ms": round(elapsed * 1000, 1),
        }
    except Exception as e:
        return {"response": f"ERROR: {e}", "tokens": 0, "latency_ms": 0}


def main():
    cases = load_cases()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for model in MODELS:
        safe_name = model.replace(":", "_").replace("/", "_")
        out_path = OUTPUT_DIR / f"eval_v1_{safe_name}.jsonl"
        print(f"\n=== Running {model} ({len(cases)} cases) ===")

        with open(out_path, "w") as f:
            for i, case in enumerate(cases):
                result = call_ollama(case["prompt"], model)
                entry = {
                    "case_id": case["id"],
                    "category": case["category"],
                    "difficulty": case["difficulty"],
                    "prompt": case["prompt"],
                    "expected_behavior": case["expected_behavior"],
                    "response": result["response"],
                    "tokens": result["tokens"],
                    "latency_ms": result["latency_ms"],
                    "model": model,
                    "backend": "ollama",
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

                if (i + 1) % 10 == 0:
                    print(
                        f"  [{i + 1}/{len(cases)}] done — last: {result['latency_ms']:.0f}ms"
                    )

        # Summary
        total_latency = 0
        total_tokens = 0
        count = 0
        with open(out_path) as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    if not r["response"].startswith("ERROR"):
                        total_latency += r["latency_ms"]
                        total_tokens += r["tokens"]
                        count += 1

        if count:
            print(f"  Avg latency: {total_latency / count:.0f}ms")
            print(f"  Avg tokens: {total_tokens / count:.0f}")
            print(f"  Total time: {total_latency / 1000:.1f}s")

        print(f"  Results: {out_path}")

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
