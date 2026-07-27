#!/usr/bin/env python3
"""R14 cloud model evaluation via OpenRouter."""

import json, sys, time, urllib.request
from pathlib import Path

CORPUS = Path("cases/corpus.jsonl")
OLLAMA = "http://127.0.0.1:11434"

model = sys.argv[1] if len(sys.argv) > 1 else "deepseek/deepseek-v4-pro"
backend = sys.argv[2] if len(sys.argv) > 2 else "openrouter"
output = (
    Path(sys.argv[3])
    if len(sys.argv) > 3
    else Path(f"traces/apex-r14/{model.replace('/', '_').replace(':', '_')}.jsonl")
)

if backend == "openrouter":
    import os

    api_key = os.environ.get(
        "OPENROUTER_API_KEY", os.environ.get("OPENCODE_OPENROUTER_API_KEY", "")
    )
    base_url = "https://openrouter.ai/api/v1/chat/completions"
else:
    api_key = ""
    base_url = f"{OLLAMA}/api/generate"

cases = []
with open(CORPUS) as f:
    for line in f:
        if line.strip():
            cases.append(json.loads(line))
print(f"Loaded {len(cases)} cases, model={model}", flush=True)

output.parent.mkdir(parents=True, exist_ok=True)
start = time.time()
with open(output, "w") as out:
    for i, case in enumerate(cases):
        if backend == "openrouter":
            payload = json.dumps(
                {
                    "model": model,
                    "messages": [{"role": "user", "content": case["prompt"]}],
                    "max_tokens": 256,
                    "temperature": 0,
                }
            ).encode()
            req = urllib.request.Request(
                base_url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
            )
        else:
            payload = json.dumps(
                {
                    "model": model,
                    "prompt": case["prompt"],
                    "stream": False,
                    "options": {"num_predict": 256, "temperature": 0},
                }
            ).encode()
            req = urllib.request.Request(
                base_url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                },
            )

        try:
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
            latency = (time.time() - t0) * 1000
            if backend == "openrouter":
                response = result["choices"][0]["message"]["content"]
                tokens = result.get("usage", {}).get("total_tokens", 0)
            else:
                response = result.get("response", "")
                tokens = result.get("eval_count", 0)
        except Exception as e:
            response = f"ERROR: {e}"
            tokens = 0
            latency = 0
            print(f"  ERROR case {i}: {e}", flush=True)

        entry = {
            "case_id": case["id"],
            "category": case.get("category", "unknown"),
            "difficulty": case.get("difficulty", 3),
            "response": response,
            "tokens": tokens,
            "latency_ms": round(latency, 1),
            "model": model,
            "backend": backend,
        }
        out.write(json.dumps(entry, ensure_ascii=False) + "\n")
        out.flush()

        if (i + 1) % 25 == 0:
            elapsed = time.time() - start
            print(f"  [{i + 1}/{len(cases)}] {elapsed:.0f}s elapsed", flush=True)

total = time.time() - start
print(f"\nDone: {len(cases)} cases in {total:.0f}s ({total / len(cases):.1f}s/case)")
print(f"Output: {output}")
