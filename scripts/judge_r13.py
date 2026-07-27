#!/usr/bin/env python3
"""R13 judge — judge R12 eval output against corpus."""

import json, sys, time, urllib.request
from pathlib import Path

CORPUS = Path("/tmp/corpus.jsonl")
EVAL = Path("/home/djimit/openmythos/traces/apex-r13/r13_full.jsonl")
OUTPUT = Path("/home/djimit/openmythos/traces/apex-r13/judged_r13.jsonl")
OLLAMA = "http://127.0.0.1:11434"
JUDGE_MODEL = "qwen2.5-coder:7b"

# Load corpus
corpus = {}
with open(CORPUS) as f:
    for line in f:
        if line.strip():
            c = json.loads(line)
            corpus[c["id"]] = c
print(f"Corpus: {len(corpus)} cases")

# Load eval
evals = []
with open(EVAL) as f:
    for line in f:
        if line.strip():
            evals.append(json.loads(line))
print(f"Eval: {len(evals)} responses")


# Judge
def call_judge(prompt):
    payload = json.dumps(
        {
            "model": JUDGE_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 256, "temperature": 0},
        }
    ).encode()
    req = urllib.request.Request(
        f"{OLLAMA}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result.get("response", "")
    except Exception as e:
        return f"ERROR: {e}"


start = time.time()
judged = []
for i, ev in enumerate(evals):
    case_id = ev["case_id"]
    case = corpus.get(case_id, {})
    expected = case.get("expected_behavior", "")
    response = ev.get("response", "")

    judge_prompt = f"""Rate the following AI response on a scale of 1-5.

Question: {ev.get("prompt", "")[:300]}

Expected behavior: {expected[:200]}

AI Response: {response[:500]}

Rate 1 (bad) to 5 (excellent). Reply with ONLY a number."""

    verdict = call_judge(judge_prompt)

    # Extract score
    score = 3  # default
    for char in verdict:
        if char in "12345":
            score = int(char)
            break

    judged.append(
        {
            "case_id": case_id,
            "category": ev.get("category", "unknown"),
            "difficulty": ev.get("difficulty", 3),
            "model": "openmythos-r12-v2",
            "judge_model": JUDGE_MODEL,
            "score": score,
            "judge_verdict": verdict[:200],
            "latency_ms": ev.get("latency_ms", 0),
        }
    )

    if (i + 1) % 50 == 0:
        elapsed = time.time() - start
        avg = sum(j["score"] for j in judged) / len(judged)
        print(f"  [{i + 1}/{len(evals)}] avg={avg:.2f} {elapsed:.0f}s")

# Save
with open(OUTPUT, "w") as f:
    for j in judged:
        f.write(json.dumps(j, ensure_ascii=False) + "\n")

total = time.time() - start
avg_score = sum(j["score"] for j in judged) / len(judged)
pass_rate = sum(1 for j in judged if j["score"] >= 4) / len(judged)

print(f"\nDone: {len(judged)} cases in {total:.0f}s")
print(f"Avg score: {avg_score:.3f}")
print(f"Pass rate (>=4): {pass_rate:.1%}")
print(f"Output: {OUTPUT}")
