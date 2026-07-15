# OpenMythos R40 Alternative-Prefix Control

Decision: `diagnostic_complete`.

## Configuration

- Detached candidate source: Djimitflo
  `23824b012b17cdc8f57ffa3eeba2273feb9b8c85`.
- Candidate image: `djimitflo:r40-alternative-prefix-23824b01`
  (`sha256:b58de00d50f0721dcaae382acf9e136237ba8095228450217c1d61b5aeadee48`).
- Sidecar SHA-256:
  `3ca2224e44d4f907b2b28af927fc40bb2886fd3b2e8ff512ff41f3c998e7ffd0`.
- Subject: `qwen2.5:14b-instruct-q4_K_M`, temperature 0, seed 0,
  `num_predict` 1024.
- Djimitflo worker concurrency: 1. Ollama `OLLAMA_NUM_PARALLEL`: 1.
- Per condition: one excluded warm-up plus five measured repeats.
- Production was not changed, restarted, or promoted.

## Prefix Control

R40 held target position, total case count, category counts, corpus order, and
oracle-only scoring fixed. Within each category it selected the nearest
oracle-anchored corpus predecessors absent from R39, then filled unavoidable
shortages with the nearest R39 predecessors.

This replaced the maximum 17 cases in each prefix. Position 46 retained 28 of
45 R39 prefix cases; position 48 retained 30 of 47. Prompt characters changed
from 5847 to 5616 and from 5946 to 5715 respectively.

The position-46 request SHA-256 was
`f90e5b1a3451a7704caa7e325eb2a072c6b2ff1121404960e1b36e0f6de0f882`.
The position-48 request SHA-256 was
`1088472b2b058f6dabfab75dcf39c762018ed4906558ab1b1670d63d6d34a2c4`.

## Results

All 12 calls completed every selected case, used oracle scoring throughout,
kept each case below 120 seconds, preserved target position and model
residency, and left candidate and production healthy. Target provenance was
10/10 across measured calls.

### cross-lingual-007 at position 46

- Within-condition classification: `stable`.
- R39 relation: `matches_r39_exact_prefix`.
- Unique measured hashes: 1/5.
- Unique measured outcomes: 1 (`false`).
- All five measured calls and the excluded warm-up produced hash
  `0d28ed4397b91b2dea18d3d88cc730294099629374009ba3b7eaa0d54855f750`.
- The R38 isolated baseline pair was not observed.

### cross-lingual-009 at position 48

- Within-condition classification: `variable`.
- R39 relation: `matches_r39_exact_prefix`.
- Unique measured hashes: 2/5.
- Unique measured outcomes: 2 (`true`, `false`).
- Measured outcomes were `true`, `true`, `false`, `true`, `true`.
- Hash
  `6cb7a5fc0806d8d5e0502f20ff41b823b797dd9afe855781042bf851a199c0a5`
  mapped to `true`; hash
  `10441c204421f18ba298143bc61c428f92ff1454791eff96e9bce54b9ca45168`
  mapped to `false`.
- The R38 isolated baseline pair was observed.

## Decision Boundary

Replacing every available category-matched alternative under the 90-anchor
constraint did not change either R39 target support set. R40 therefore found
no prefix-identity signal among the 17 replaced cases. It does not prove a
pure position effect because 28 and 30 R39 prefix cases remained shared.
Absolute position, cumulative inference load, or one of those shared cases
remains plausible.

No result qualifies source, sidecar, model, policy, or production promotion.
The next smallest experiment is a preregistered nested-prefix position sweep
using only existing oracle-anchored R39 cases. It should locate whether the
observed support changes across shorter positions before any new anchors or
runtime changes are proposed.

The candidate container, image, database copies, temporary environment,
detached worktree, runner state, and staged sidecar were removed. R35
production remained healthy with restart policy `unless-stopped`, restart
count zero, both databases at integrity `ok`, and the unchanged 78-anchor
sidecar. One handled R35 heartbeat lock skip occurred; no fatal or unhandled
database lock was observed.

Machine-readable evidence is in `r40-evidence/classification.json`; its SHA-256
is `4231e780e244e58092a5b19481422b7f087674eee2c4499913ac85c9aeacd252`.
