#!/usr/bin/env python3
"""APEX R46 — held-out validation of the per-category selector choice.

R45's 57.7% "selective hybrid" was overfit: it chose which categories to apply
the content discriminator to using the same 78 cases it scored on. R46 removes
that leak with repeated random 50/50 splits:

  - each case carries its outcome under BOTH policies (from R45):
      disc_pass  = content discriminator (R45 selectors)
      route_pass = R43 category routing
  - TRAIN half: per category, pick whichever policy has the higher pass rate
  - TEST half: apply that per-category choice, score on held-out cases
  - repeat over many random splits; report mean held-out pass rate

Baselines scored on the SAME test halves: always-route (R43) and always-disc.
A learned policy only "wins" if it beats always-route out of sample.
"""
import json, random
from collections import defaultdict

rows = json.load(open('/private/tmp/claude-501/-Users-dlandman-djimitflo/67c701c0-e7fa-4b23-ad1c-fdad12ffb826/scratchpad/apex-r45-results.json'))['rows']
for r in rows:
    r['disc'] = 1 if r['chosenPass'] else 0
    r['route'] = 1 if r['r43Pass'] else 0

by_cat = defaultdict(list)
for r in rows:
    by_cat[r['category']].append(r)

def run_split(seed):
    rng = random.Random(seed)
    train, test = [], []
    for cat, items in by_cat.items():
        idx = list(range(len(items)))
        rng.shuffle(idx)
        half = len(idx) // 2
        for i in idx[:half]: train.append(items[i])
        for i in idx[half:]: test.append(items[i])
    # learn per-category policy on train
    policy = {}
    tr = defaultdict(lambda: [0, 0])  # cat -> [disc_sum, route_sum]
    for r in train:
        tr[r['category']][0] += r['disc']
        tr[r['category']][1] += r['route']
    for cat in by_cat:
        d, ro = tr[cat]
        policy[cat] = 'disc' if d > ro else 'route'  # ties -> route (conservative)
    # score on held-out test
    learned = sum(r['disc'] if policy[r['category']] == 'disc' else r['route'] for r in test)
    always_route = sum(r['route'] for r in test)
    always_disc = sum(r['disc'] for r in test)
    n = len(test)
    return learned / n, always_route / n, always_disc / n

N = 2000
L = R = D = 0.0
wins = 0
for s in range(N):
    l, r, d = run_split(s)
    L += l; R += r; D += d
    if l > r + 1e-9: wins += 1
print(f"repeated 50/50 splits: {N}")
print(f"  learned per-category policy (held-out): {L/N:.3f}")
print(f"  always-route baseline    (held-out): {R/N:.3f}")
print(f"  always-disc baseline     (held-out): {D/N:.3f}")
print(f"  splits where learned > route: {wins}/{N} = {wins/N:.1%}")
print()
# stability of the learned choice across full data (which categories consistently prefer disc)
full = defaultdict(lambda: [0, 0])
for r in rows:
    full[r['category']][0] += r['disc']
    full[r['category']][1] += r['route']
print("per-category full-data pass (disc vs route):")
for cat in sorted(full):
    d, ro = full[cat]
    n = len(by_cat[cat])
    flag = 'disc' if d > ro else ('route' if ro > d else 'tie')
    print(f"  {cat:20} disc {d}/{n}  route {ro}/{n}  -> {flag}")
