# OpenMythos R39 Exact-Prefix Position

Decision: `diagnostic_complete`.

## Configuration

- Detached candidate source: Djimitflo
  `23824b012b17cdc8f57ffa3eeba2273feb9b8c85`.
- Candidate image: `djimitflo:r39-exact-prefix-23824b01`
  (`sha256:b58de00d50f0721dcaae382acf9e136237ba8095228450217c1d61b5aeadee48`).
- Sidecar SHA-256:
  `3ca2224e44d4f907b2b28af927fc40bb2886fd3b2e8ff512ff41f3c998e7ffd0`.
- Subject: `qwen2.5:14b-instruct-q4_K_M`, temperature 0, seed 0,
  `num_predict` 1024.
- Djimitflo worker concurrency: 1. Ollama `OLLAMA_NUM_PARALLEL`: 1.
- Per condition: the exact R37 prefix, one excluded warm-up, then five
  measured repetitions.
- Production was not changed, restarted, or promoted.

## Protocol Correction

The initial preregistration treated request-list indices as execution order.
One excluded 21-case call proved that `case_ids` is membership-only and corpus
order controls execution. Its last result was `hallucination-apex-004`, not the
intended target. The call was classified invalid with zero accepted warm-ups
and zero accepted measurements.

The protocol was corrected and pushed before valid execution. The R37 API
responses place `cross-lingual-007` at position 46 and `cross-lingual-009` at
position 48. The valid requests were generated directly from those R37 result
prefixes.

## Results

All 12 valid calls completed every selected case, used oracle scoring, kept
each case below 120 seconds, preserved target position and model residency,
and left candidate and production healthy. Target provenance was 10/10 across
the measured calls.

### cross-lingual-007 at position 46

- Classification: `stable_prefix_shift`.
- Unique measured hashes: 1/5.
- Unique measured outcomes: 1 (`false`).
- All measured calls and the excluded warm-up produced hash
  `0d28ed4397b91b2dea18d3d88cc730294099629374009ba3b7eaa0d54855f750`.
- The R38 isolated baseline was hash
  `bd1513dbedb497629e1e19cf76549061fce0bc29dc2840cd07eb0538f500f809`
  with outcome `true`.
- The prefix hash equals the R37 warm-up and R32 variant. Exact-prefix context
  therefore produced a repeatable shift from the isolated response.

### cross-lingual-009 at position 48

- Classification: `reproduced_context_variance`.
- Unique measured hashes: 2/5.
- Unique measured outcomes: 2 (`true`, `false`).
- Measured outcomes were `true`, `true`, `true`, `true`, `false`.
- The `true` hash
  `6cb7a5fc0806d8d5e0502f20ff41b823b797dd9afe855781042bf851a199c0a5`
  equals the R38 isolated baseline.
- The `false` hash
  `10441c204421f18ba298143bc61c428f92ff1454791eff96e9bce54b9ca45168`
  equals the excluded R39 warm-up plus the R37 warm-up and R32 variant.
- R39 reproduced R37 outcome variance but not every previously observed text
  variant.

## Decision Boundary

R39 shows that the exact R37 prefix and execution position are sufficient to
recover both a stable context shift and measured context variance that were
absent under R38 isolation. It does not distinguish prefix identity, absolute
position, or cumulative inference state as the causal mechanism.

No result qualifies source, sidecar, model, policy, or production promotion.
A next experiment must hold target position fixed while replacing the exact
prefix with a length-matched alternative prefix. That is the smallest test
that separates position from prefix identity without changing runtime code.

The candidate container, image, database copies, temporary environment,
detached worktree, runner state, and staged sidecar were removed. R35
production remained healthy with restart policy `unless-stopped`, restart
count zero, both databases at integrity `ok`, and the unchanged 78-anchor
sidecar. One handled R35 heartbeat lock skip occurred; no fatal or unhandled
database lock was observed.

Machine-readable evidence is in `r39-evidence/classification.json`; its SHA-256
is `ad17743d7a3ab8c30c776ab43b3235a0e3fadc2b755a109135adf6afe5f196f3`.
