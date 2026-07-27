#!/usr/bin/env python3
"""R13 final leaderboard — R9 vs R10 vs R12."""

import json
from pathlib import Path

traces = {
    "R9 qwen2.5-coder:7b": "/Users/dlandman/OpenMythos/openmythos-benchmark/traces/apex-r9-full/judged_qwen2_5_coder_7b.jsonl",
    "R10 gemma-4-26b": "/Users/dlandman/OpenMythos/openmythos-benchmark/traces/apex-r10-governance/judged_gemma_4_26b.jsonl",
    "R12 openmythos-r12-v2": "/home/djimit/openmythos/traces/apex-r13/judged_r13.jsonl",
}

results = []
for name, path in traces.items():
    p = Path(path)
    if not p.exists():
        # Try via ssh
        continue
    scores = []
    cats = {}
    with open(p) as f:
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
            "categories": {
                c: round(sum(v) / len(v), 2) for c, v in sorted(cats.items())
            },
        }
    )

# Sort by avg score
results.sort(key=lambda x: -x["avg"])

print("# APEX R13 Final Leaderboard\n")
print(f"| Rank | Model | Cases | Avg Score | Pass Rate |")
print(f"|------|-------|------:|----------:|----------:|")
for i, r in enumerate(results, 1):
    print(
        f"| {i} | {r['model']} | {r['cases']} | {r['avg']:.3f} | {r['pass_rate']:.1%} |"
    )

print("\n## Category Breakdown\n")
all_cats = sorted(set(c for r in results for c in r["categories"]))
print(f"| Model | {' | '.join(all_cats)} |")
print(f"|-------|{'------|' * len(all_cats)}")
for r in results:
    vals = [r["categories"].get(c, "-") for c in all_cats]
    print(f"| {r['model']} | {' | '.join(str(v) for v in vals)} |")
