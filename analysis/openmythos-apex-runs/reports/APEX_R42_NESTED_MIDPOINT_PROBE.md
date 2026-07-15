# OpenMythos R42 Nested Midpoint Probe

Decision: `diagnostic_complete`.

## Configuration

- Detached candidate source: Djimitflo
  `23824b012b17cdc8f57ffa3eeba2273feb9b8c85`.
- Rebuilt candidate image: `djimitflo:r42-nested-midpoint-23824b01`
  (`sha256:e6fb82e235951d1c0420efe6813cb4102de876dbc18f76ed4e4da5e0f8ce04f9`).
- Sidecar SHA-256:
  `3ca2224e44d4f907b2b28af927fc40bb2886fd3b2e8ff512ff41f3c998e7ffd0`.
- Subject: `qwen2.5:14b-instruct-q4_K_M`, temperature 0, seed 0,
  `num_predict` 1024.
- Djimitflo worker concurrency: 1. Ollama `OLLAMA_NUM_PARALLEL`: 1.
- Per condition: one excluded warm-up plus five measured repeats.
- Production was not changed, restarted, or promoted.

## Nested Selection

Each midpoint retained the nearest `position - 1` cases from its published
R41 prefix and appended the target in corpus order. Both suffix relations were
machine-verified and every selected case was oracle-anchored.

| Target | Position | Prefix cases | Prompt characters | Request SHA-256 |
| --- | ---: | ---: | ---: | --- |
| `cross-lingual-007` | 8 | 7 | 479 | `6992e4fc45f746fc96469bec19a6a3deee8ddb63702c76954d3c1ba070496f0a` |
| `cross-lingual-009` | 24 | 23 | 1531 | `96f49769a19fa3289763cda15c6b67440e69e3248e719a1fc9920f2464644eb7` |

All 12 calls completed every selected case, used oracle scoring throughout,
kept each case below 120 seconds, preserved target position and model
residency, and left candidate and production healthy. Target provenance was
10/10 across measured calls.

## Results

### cross-lingual-007 at position 8

The condition was `stable` and `matches_upper`. All five measured calls and
the excluded warm-up produced hash
`0d28ed4397b91b2dea18d3d88cc730294099629374009ba3b7eaa0d54855f750`
with outcome `false`, exactly matching the R41 position-16 support.

| Position | Origin | Support |
| ---: | --- | --- |
| 1 | R38 | `bd1513...f809`, `true` |
| 8 | R42 | `0d28ed...f750`, `false` |
| 16 | R41 | `0d28ed...f750`, `false` |

The observed `cross-lingual-007` support departure is narrowed from positions
1 through 16 to positions 1 through 8. This remains a finite descriptive
interval, not a monotonic or causal threshold.

### cross-lingual-009 at position 24

The condition was `variable` and `matches_neither`. Measured outcomes were
`true`, `false`, `false`, `true`, `false` with three response hashes:

- `6cb7a5fc0806d8d5e0502f20ff41b823b797dd9afe855781042bf851a199c0a5`
  mapped to `true` in runs 1 and 4;
- `c048a9838cfe1ca5ee4638c0682574ed6a8c6daaeeb9ce49f64248ec9811d82e`
  mapped to `false` in run 2;
- `10441c204421f18ba298143bc61c428f92ff1454791eff96e9bce54b9ca45168`
  mapped to `false` in runs 3 and 5.

The `c048a9...d82e` response occurred previously in R37 but belongs to neither
fixed R41 endpoint support. Position 24 therefore cannot narrow the position
16-to-32 interval by exact support equality.

| Position | Origin | Support |
| ---: | --- | --- |
| 16 | R41 | `6cb7...c0a5`, `true` |
| 24 | R42 | `6cb7...c0a5`, `true`; `c048...d82e`, `false`; `10441...5168`, `false` |
| 32 | R41 | `6cb7...c0a5`, `true`; `10441...5168`, `false` |

## Decision Boundary

R42 supports one narrower descriptive interval for `cross-lingual-007`, but
rejects simple midpoint refinement for `cross-lingual-009`. The position-24
support is a strict expansion of the position-32 endpoint support in these
five measurements. No monotonic position threshold may be inferred.

No result qualifies source, sidecar, model, policy, or production promotion.
Further midpoint bisection for `cross-lingual-009` should stop. If this line of
investigation continues, the smallest justified experiment is a
preregistered position-24 order/session-state control that runs that condition
first and compares its complete support with R42. It must preserve the same
source and policy and must not promote from finite support discovery.

The candidate container, image tag, database copies, temporary environment,
detached worktree, runner state, and staged sidecar were removed. R35
production remained healthy with restart policy `unless-stopped`, restart
count zero, all five production databases at integrity `ok`, and the
unchanged 78-anchor sidecar. One handled R35 heartbeat lock skip occurred; no
fatal or unhandled database lock was observed.

Machine-readable evidence is in `r42-evidence/classification.json`; its
SHA-256 is `0891158d23be7e2ff1f23fe84017e933b0338217b076d13c1be800e31204ec55`.
