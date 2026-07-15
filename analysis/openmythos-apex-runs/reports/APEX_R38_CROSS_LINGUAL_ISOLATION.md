# OpenMythos R38 Cross-Lingual Isolation

Decision: `diagnostic_complete`.

## Configuration

- Detached candidate source: Djimitflo
  `23824b012b17cdc8f57ffa3eeba2273feb9b8c85`.
- Candidate image: `djimitflo:r38-cross-lingual-23824b01`
  (`sha256:b58de00d50f0721dcaae382acf9e136237ba8095228450217c1d61b5aeadee48`).
- Sidecar SHA-256:
  `3ca2224e44d4f907b2b28af927fc40bb2886fd3b2e8ff512ff41f3c998e7ffd0`.
- Subject: `qwen2.5:14b-instruct-q4_K_M`, temperature 0, seed 0,
  `num_predict` 1024.
- Djimitflo worker concurrency: 1. Ollama `OLLAMA_NUM_PARALLEL`: 1.
- Fixed phase order: `cross-lingual-007`, then `cross-lingual-009`.
- Per phase: one excluded single-case warm-up plus five measured repeats.
- Production was not changed, restarted, or promoted.

## Results

All 12 API calls completed 1/1, used oracle scoring, finished within six
seconds, preserved model residency, and left candidate and production healthy.

### cross-lingual-007

- Classification: `not_reproduced_in_isolation`.
- Unique measured response hashes: 1/5.
- Unique measured oracle outcomes: 1 (`true`).
- The excluded warm-up hash and outcome matched all measured calls.
- The measured hash was already observed among the R37 variants.

### cross-lingual-009

- Classification: `not_reproduced_in_isolation`.
- Unique measured response hashes: 1/5.
- Unique measured oracle outcomes: 1 (`true`).
- The excluded warm-up differed from all measured calls in both response hash
  and oracle outcome (`false` versus measured `true`).
- The measured hash was already observed among the R37 variants.

## Decision Boundary

R38 did not reproduce intrinsic measured instability when either case was run
alone. The evidence makes 60-case batch or position context the leading
hypothesis for the R37 mismatch, but it does not prove a specific mechanism.
Neither classification qualifies source, sidecar, model, or production
promotion.

Any next experiment must pre-register case position or fixed-prefix context as
its independent variable. It must not reinterpret R37 as passing or treat five
stable isolated repeats as full-workload determinism.

The candidate container, image, database copies, temporary environment,
detached worktree, runner state, and staged sidecar were removed. R35
production remained healthy with restart policy `unless-stopped`, database
integrity `ok`, clean logs, and the unchanged 78-anchor sidecar.

Machine-readable evidence is in `r38-evidence/classification.json`; its SHA-256
is `07310e17e65b547755dd9191182b803ba827baa776eaf19f0da47e3b56dd3ff2`.
