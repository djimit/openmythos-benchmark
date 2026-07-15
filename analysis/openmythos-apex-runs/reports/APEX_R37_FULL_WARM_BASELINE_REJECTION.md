# OpenMythos R37 Full Warm Baseline Rejection

Decision: `rejected`.

## Configuration

- Detached candidate source: Djimitflo
  `23824b012b17cdc8f57ffa3eeba2273feb9b8c85`.
- Candidate image: `djimitflo:r37-full-warm-23824b01`
  (`sha256:b58de00d50f0721dcaae382acf9e136237ba8095228450217c1d61b5aeadee48`).
- Sidecar: 90 unique anchors, zero skipped cases,
  `3ca2224e44d4f907b2b28af927fc40bb2886fd3b2e8ff512ff41f3c998e7ffd0`.
- Subject: `qwen2.5:14b-instruct-q4_K_M`, temperature 0, seed 0,
  `num_predict` 1024.
- Djimitflo worker concurrency: 1. Ollama `OLLAMA_NUM_PARALLEL`: 1.
- Independent variable: one excluded, identical 60-case warm-up before three
  measured runs.
- Production was not changed, restarted, or promoted.

## Warm-Up

The excluded warm-up run `116e2a30-66b1-4dad-9368-a556c2f0f605`
completed 60/60 cases with 60/60 oracle sources in 155 seconds. `ollama ps`
confirmed that the exact subject model was resident before measurement.

As context only, the warm-up matched each measured run for 48/60 response
hashes. Its differences included the two later measured hash mismatches,
`cross-lingual-007` and `cross-lingual-009`. Warm-up hashes remained excluded
from acceptance as pre-registered.

## Measured Results

The measured runs completed 60/60 cases with 60/60 oracle sources in 153, 152,
and 164 seconds:

- `b8348e9f-d871-4d34-9e45-65d24945dfc7`
- `f00e605a-1f82-4a5f-bf82-1a590bfd6c76`
- `03103426-2fa1-4212-adca-da86d4cf8408`

Completion, oracle provenance, resident-model, and duration gates passed.
Mandatory response-hash parity failed:

- Run 1 versus run 2: 59/60.
- Run 1 versus run 3: 59/60.
- Run 2 versus run 3: 58/60.
- Mismatching cases: `cross-lingual-007` and `cross-lingual-009`.

Independent R32 oracle outcomes matched 172/180. `contradiction-002` and
`cross-lingual-007` differed in all three measured runs;
`cross-lingual-009` differed in runs 1 and 2. The authoritative outcome map
uses the 48 anchored R32 rows plus the independent 12-case R34 overlay for the
historical R32 JudgeService fallbacks.

For context only, each measured run matched 48/60 R32 response hashes. R32
response parity was not an acceptance gate because R37 changed scoring
coverage and execution schedule.

## Decision

The one-workload warm-state protocol qualified by R36 does not generalize to
the canonical 60-case baseline. R37 therefore rejects the full warm candidate
and does not authorize source reapplication, sidecar promotion, or production
promotion. R36 remains a valid narrow 12-case result and is not reinterpreted.

Any follow-up must pre-register a narrower cross-lingual nondeterminism
experiment or a different evidence invariant. It must not weaken R37 after
observing these mismatches.

The candidate container, image, database copies, temporary environment,
detached worktree, runner state, and staged sidecar were removed. R35
production remained healthy with restart policy `unless-stopped`, database
integrity `ok`, clean logs, and the unchanged 78-anchor sidecar.

Machine-readable evidence is in `r37-evidence/parity.json`; its SHA-256 is
`399e1b4eb192c64d2b19e5e11f6e45d1434a9525b01885a971f3dd3e49d99abf`.
