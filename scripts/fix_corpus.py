#!/usr/bin/env python3
"""Fix OpenMythos corpus by removing prompt-intel cases and validating."""

import json
from pathlib import Path

CORPUS_PATH = Path(__file__).parent.parent / "cases" / "corpus.jsonl"

# Load
cases = []
removed = 0
with CORPUS_PATH.open() as f:
    for line in f:
        line = line.strip()
        if line:
            c = json.loads(line)
            if c.get("author") != "prompt-intel-pipeline":
                cases.append(c)
            else:
                removed += 1

# Write clean
with CORPUS_PATH.open("w") as f:
    for c in cases:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")

print(f"Removed: {removed} prompt-intel cases")
print(f"Remaining: {len(cases)} cases")

# Verify categories
cats = {}
for c in cases:
    cat = c.get("category", "?")
    cats[cat] = cats.get(cat, 0) + 1

print(f"Categories: {len(cats)}")
for cat, n in sorted(cats.items()):
    status = "OK" if n >= 25 else "LOW"
    print(f"  {cat:25s} {n:3d} [{status}]")

# Verify IDs
import re

pattern = re.compile(r"^[a-z][a-z-]*-\d{3}$")
bad_ids = [c.get("id") for c in cases if not pattern.match(c.get("id", ""))]
if bad_ids:
    print(f"\nWARNING: {len(bad_ids)} IDs don't match schema:")
    for bid in bad_ids[:5]:
        print(f"  {bid}")
else:
    print(f"\nAll {len(cases)} IDs match schema ✓")

# Verify unique IDs
ids = [c.get("id") for c in cases]
if len(ids) != len(set(ids)):
    from collections import Counter

    dupes = [id for id, cnt in Counter(ids).items() if cnt > 1]
    print(f"\nWARNING: {len(dupes)} duplicate IDs:")
    for d in dupes[:5]:
        print(f"  {d}")
else:
    print(f"All IDs unique ✓")
