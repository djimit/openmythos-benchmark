#!/usr/bin/env python3
"""Quick judge — evaluate APEX responses using local Ollama judge."""

import json, sys, time, urllib.request
from pathlib import Path

CORPUS = Path("cases/corpus.jsonl")
JUDGE_MODEL = "qwen2.5-coder:latest"
OLLAMA = "http://127.0.0.1:11434"


def load_corpus():
    corpus = {}
    with open(CORPUS) as f:
        for line in f:
            if line.strip():
                c = json.loads(line)
                corpus[c["id"]] = c
    return corpus


def call_judge(prompt):
    payload = json.dumps(
        {
            "model": JUDGE_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 128, "temperature": 0},
        }
    ).encode()
    req = urllib.request.Request(
        f"{OLLAMA}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            return result.get("response", "")
    except Exception as e:
        return f"ERROR: {e}"


def judge_eval(eval_path, output_path, model_name):
    corpus = load_corpus()
    evals = []
    with open(eval_path) as f:
        for line in f:
            if line.strip():
                evals.append(json.loads(line))

    print(f"Judging {len(evals)} responses for {model_name}...", flush=True)
    judged = []
    for i, ev in enumerate(evals):
        case = corpus.get(ev["case_id"], {})
        expected = case.get("expected_behavior", "")
        response = ev.get("response", "") or ""

        if response.startswith("ERROR"):
            score = 1
            verdict = "ERROR in response"
        else:
            prompt = f"""Rate this AI response on a scale of 1-5.

Question: {case.get("prompt", "")[:300]}

Expected: {expected}

Response: {response[:400]}

Rate 1 (bad) to 5 (excellent). Reply with ONLY a number."""

            verdict = call_judge(prompt)
            score = 3
            for char in verdict:
                if char in "12345":
                    score = int(char)
                    break

        judged.append(
            {
                "case_id": ev["case_id"],
                "category": ev.get("category", "unknown"),
                "model": model_name,
                "score": score,
            }
        )

        if (i + 1) % 50 == 0:
            avg = sum(j["score"] for j in judged) / len(judged)
            print(f"  [{i + 1}/{len(evals)}] avg={avg:.2f}", flush=True)

    with open(output_path, "w") as f:
        for j in judged:
            f.write(json.dumps(j) + "\n")

    avg = sum(j["score"] for j in judged) / len(judged)
    passed = sum(1 for j in judged if j["score"] >= 4) / len(judged)
    print(f"\n{model_name}: avg={avg:.3f} pass={passed:.1%}", flush=True)
    return avg, passed


if __name__ == "__main__":
    eval_path = sys.argv[1]
    output_path = sys.argv[2]
    model_name = sys.argv[3]
    judge_eval(Path(eval_path), Path(output_path), model_name)
