#!/usr/bin/env python3
"""R13 evaluation: run corpus against openmythos-r12 via local Ollama."""

import json, sys, time, urllib.request
from pathlib import Path

CORPUS = Path("/tmp/corpus.jsonl")
OUTPUT = Path("/home/djimit/openmythos/traces/apex-r13/r13_full.jsonl")
OLLAMA = "http://127.0.0.1:11434"
MODEL = "openmythos-r12-v2"

# Load corpus
cases = []
with open(CORPUS) as f:
    for line in f:
        if line.strip():
            cases.append(json.loads(line))
print(f"Loaded {len(cases)} cases")

# Check Ollama
try:
    req = urllib.request.Request(f"{OLLAMA}/api/tags")
    with urllib.request.urlopen(req, timeout=10) as resp:
        models = json.loads(resp.read())
        model_names = [m["name"] for m in models.get("models", [])]
        # Match with or without :latest suffix
        matched = any(
            MODEL == name or MODEL + ":latest" == name for name in model_names
        )
        if not matched:
            print(f"ERROR: {MODEL} not found. Available: {model_names}")
            sys.exit(1)
        print(f"Ollama OK: {MODEL} found")
except Exception as e:
    print(f"ERROR: Cannot reach Ollama: {e}")
    sys.exit(1)

# Run evaluation
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
start = time.time()
with open(OUTPUT, "w") as out:
    for i, case in enumerate(cases):
        payload = json.dumps(
            {
                "model": MODEL,
                "prompt": case["prompt"],
                "stream": False,
                "options": {"num_predict": 256, "temperature": 0},
            }
        ).encode()

        try:
            req = urllib.request.Request(
                f"{OLLAMA}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=300) as resp:
                result = json.loads(resp.read())
            latency = (time.time() - t0) * 1000
            response = result.get("response", "")
            tokens = result.get("eval_count", 0)
        except Exception as e:
            response = f"ERROR: {e}"
            tokens = 0
            latency = 0
            print(f"  ERROR on case {i}: {e}", flush=True)

        entry = {
            "case_id": case["id"],
            "category": case.get("category", "unknown"),
            "difficulty": case.get("difficulty", 3),
            "response": response,
            "tokens": tokens,
            "latency_ms": round(latency, 1),
            "model": MODEL,
            "backend": "ollama",
        }
        out.write(json.dumps(entry, ensure_ascii=False) + "\n")
        out.flush()

        if (i + 1) % 25 == 0:
            elapsed = time.time() - start
            print(f"  [{i + 1}/{len(cases)}] {elapsed:.0f}s elapsed")

total = time.time() - start
print(f"\nDone: {len(cases)} cases in {total:.0f}s ({total / len(cases):.1f}s/case)")
