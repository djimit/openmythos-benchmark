# OpenMythos R41 Nested-Prefix Position Sweep

Decision: `diagnostic_complete`.

## Configuration

- Detached candidate source: Djimitflo
  `23824b012b17cdc8f57ffa3eeba2273feb9b8c85`.
- Candidate image: `djimitflo:r41-nested-prefix-23824b01`
  (`sha256:b58de00d50f0721dcaae382acf9e136237ba8095228450217c1d61b5aeadee48`).
- Sidecar SHA-256:
  `3ca2224e44d4f907b2b28af927fc40bb2886fd3b2e8ff512ff41f3c998e7ffd0`.
- Subject: `qwen2.5:14b-instruct-q4_K_M`, temperature 0, seed 0,
  `num_predict` 1024.
- Djimitflo worker concurrency: 1. Ollama `OLLAMA_NUM_PARALLEL`: 1.
- Per condition: one excluded warm-up plus five measured repeats.
- Production was not changed, restarted, or promoted.

## Nested Selection

Each condition used the nearest `position - 1` cases from the end of the
target's exact R39 prefix, followed by the target in corpus order. The
position-16 prefix is therefore an exact suffix of the longer prefix for the
same target. Every selected case was oracle-anchored.

| Target | Position | Prefix cases | Prompt characters | Request SHA-256 |
| --- | ---: | ---: | ---: | --- |
| `cross-lingual-007` | 16 | 15 | 1058 | `57ba848a03526d81be832b9d7d4930ea69fe8b93057984d2a1d5a89e145d1c36` |
| `cross-lingual-007` | 31 | 30 | 1881 | `4847ba174e2f19602af9da5962d7e58a1345793aab4eb9a24cc7831d874d22cd` |
| `cross-lingual-009` | 16 | 15 | 1038 | `ba7b54818863afa1ff55c9062c3e81923953642e9ddff04e17d5d313f15120bc` |
| `cross-lingual-009` | 32 | 31 | 1950 | `ab4412cd8e387a7561c0da5260115d501cff4e4c95d6c75c51f20df5a84ae98c` |

All 24 calls completed every selected case, used oracle scoring throughout,
kept each case below 120 seconds, preserved target position and model
residency, and left candidate and production healthy. Target provenance was
20/20 across measured calls.

## Results

### cross-lingual-007

The five measured outcomes were `false` at position 16 and `false` at
position 31. Both conditions were stable on the single response hash
`0d28ed4397b91b2dea18d3d88cc730294099629374009ba3b7eaa0d54855f750`.
Their complete measured support matched the R39 position-46 support and
differed from the R38 isolated support.

The descriptive support path is:

| Position | Origin | Support |
| ---: | --- | --- |
| 1 | R38 | `bd1513...f809`, `true` |
| 16 | R41 | `0d28ed...f750`, `false` |
| 31 | R41 | `0d28ed...f750`, `false` |
| 46 | R39 | `0d28ed...f750`, `false` |

The observed support departure lies somewhere in the tested interval from
position 1 through position 16. These finite measurements do not establish a
monotonic or causal threshold.

### cross-lingual-009

Position 16 was stable: all five measured calls produced
`6cb7a5fc0806d8d5e0502f20ff41b823b797dd9afe855781042bf851a199c0a5`
with outcome `true`, exactly matching R38 isolation. Its excluded warm-up was
the other known response and outcome, so warm-up state was not pooled into
the measured support.

Position 32 was variable. Measured outcomes were `false`, `true`, `true`,
`true`, `true`; hash `10441c204421f18ba298143bc61c428f92ff1454791eff96e9bce54b9ca45168`
mapped to `false`, and hash
`6cb7a5fc0806d8d5e0502f20ff41b823b797dd9afe855781042bf851a199c0a5`
mapped to `true`. This complete two-pair support exactly matched R39 at
position 48.

The descriptive support path is:

| Position | Origin | Support |
| ---: | --- | --- |
| 1 | R38 | `6cb7...c0a5`, `true` |
| 16 | R41 | `6cb7...c0a5`, `true` |
| 32 | R41 | `6cb7...c0a5`, `true`; `10441...5168`, `false` |
| 48 | R39 | `6cb7...c0a5`, `true`; `10441...5168`, `false` |

The observed support expansion lies somewhere in the tested interval after
position 16 through position 32. It remains finite-run evidence, not a
variance-rate estimate or proof of monotonicity.

## Decision Boundary

R41 localizes the two R39 context effects to different nested-prefix
intervals. It does not identify whether response support is driven by one or
more added cases, prompt length, absolute execution position, accumulated
inference state, or their interaction. No result qualifies source, sidecar,
model, policy, or production promotion.

The smallest next diagnostic is a preregistered nested midpoint probe at
position 8 for `cross-lingual-007` and position 24 for
`cross-lingual-009`, retaining the same endpoints and explicitly preserving
the non-monotonic interpretation. It can narrow the observed intervals but
must not be reported as binary threshold search.

The candidate container, image, database copies, temporary environment,
detached worktree, runner state, and staged sidecar were removed. R35
production remained healthy with restart policy `unless-stopped`, restart
count zero, all five production databases at integrity `ok`, and the
unchanged 78-anchor sidecar. Six handled R35 heartbeat lock skips occurred;
no fatal or unhandled database lock was observed.

Machine-readable evidence is in `r41-evidence/classification.json`; its
SHA-256 is `d0d06af452f75e270dcae55eea91d3dd85d5fb5548ea16dfe684f33aca9fda6f`.
