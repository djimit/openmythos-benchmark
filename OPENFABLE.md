# OpenFable — the living adversary for OpenMythos

OpenMythos is the **frozen canon**: 275 single-turn cases, versioned, citeable,
reproducible. Its value is that it does *not* change.

OpenFable is its **living adversary**, driven by a frontier model (Claude Fable 5
where it will play along, Claude Opus 4.8 as the robust default). It has two roles,
and both feed the same canon.

## Two roles

| Role | Script | What it does |
|------|--------|--------------|
| **Generator** | `scripts/generate.py` | A frontier model authors new schema-valid *draft* cases, targeting weak categories. Drafts enter as `validation_status: "draft"` — unverified until reviewed. |
| **Adversary** | `scripts/fable.py` | A frontier model plays an adaptive attacker that escalates over N turns against a target; a judge scores whether governance held across the whole conversation. Tests what a single-turn corpus cannot. |

## The evolution loop

```
generate.py / fable.py   →  candidate cases + adversarial scores
        │
        ▼
validate.py  →  evaluate.py  →  judge.py  →  discrimination.py
                                                   │
                        keep only cases that discriminate model quality
                                                   │
                                                   ▼
                                    promote to the OpenMythos canon (v+1)
```

`discrimination.py` is the promotion gate: a case earns a place in the canon only
if it separates strong models from weak ones. That is also the proof that version
N+1 beats N — higher discrimination, lower dead-case rate, on the same model set.

## Why "Fable"

Claude Fable 5 is the strongest adversary, and a *fable* is a generated narrative
used to test. Note: Fable's own safety classifiers sometimes **refuse to attack**
even sanctioned red-team objectives (`fable.py` handles this gracefully). A refusal
to attack is itself a signal; fall back to Opus as the attacker, or wire the
server-side `fallbacks` parameter so a refused attack is re-served by Opus.

## Provenance & honesty

Generated `references`/`real_world_analog` fields are **not verified** — a generated
citation may be fabricated (the very failure the `hallucination` category tests).
That is why generated cases are drafts. A human verifies references before promotion.
