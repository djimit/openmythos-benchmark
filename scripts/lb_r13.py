#!/usr/bin/env python3
import json

traces = {
    "R9 qwen2.5-coder:7b": "/home/djimit/openmythos/traces/apex-r9-full/judged_qwen2_5_coder_7b.jsonl",
    "R10 gemma-4-26b": "/home/djimit/openmythos/traces/apex-r10-governance/judged_gemma_4_26b.jsonl",
    "R12 openmythos-r12-v2": "/home/djimit/openmythos/traces/apex-r13/judged_r13.jsonl",
}

results = []
for name, path in traces.items():
    scores = []
    cats = {}
    with open(path) as f:
        for line in f:
            if line.strip():
                j = json.loads(line)
                score = j.get("score", j.get("judge_score", 3))
                scores.append(score)
                cat = j.get("category", "unknown")
                if cat not in cats:
                    cats[cat] = []
                cats[cat].append(score)
    avg = sum(scores) / len(scores) if scores else 0
    pass_rate = sum(1 for s in scores if s >= 4) / len(scores) if scores else 0
    results.append(
        {
            "model": name,
            "cases": len(scores),
            "avg": round(avg, 3),
            "pass_rate": round(pass_rate, 3),
            "cats": {c: round(sum(v) / len(v), 2) for c, v in cats.items()},
        }
    )

results.sort(key=lambda x: -x["avg"])

print("# APEX R13 Final Leaderboard\n")
for i, r in enumerate(results, 1):
    print(
        f"{i}. **{r['model']}**: avg={r['avg']:.3f}, pass={r['pass_rate']:.1%}, cases={r['cases']}"
    )

print("\n## Category Breakdown\n")
all_cats = sorted(set(c for r in results for c in r["cats"]))
print(f"| Model | {' | '.join(all_cats)} |")
print(f"|-------|{'------|' * len(all_cats)}")
for r in results:
    vals = [str(r["cats"].get(c, "-")) for c in all_cats]
    print(f"| {r['model']} | {' | '.join(vals)} |")
