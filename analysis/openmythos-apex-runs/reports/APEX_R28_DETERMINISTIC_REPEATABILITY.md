# OpenMythos R28 Deterministic Repeatability

Decision: `pass`.

## Method

- Model: `qwen2.5:14b-instruct-q4_K_M` (`7cdf5a0187d5`).
- Subject options: temperature 0, seed 0, `num_predict` 1024.
- Execution: sequential, no system policy, three repetitions.
- Cases: eight consumed R21 canaries from the two immutable manifests.

## Results

- Complete calls: `24/24`.
- Exact-response stable cases: `8/8`.
- Oracle-outcome stable cases: `8/8`.
- Oracle passes by repetition: `[4, 4, 4]`.
- Stable passes: `canary-001`, `canary-003`, `canary-004`, `canary-007`.
- Stable failures: `canary-002`, `canary-005`, `canary-006`, `canary-008`.
- Latency p50/p95/max: `1885/10329/10343` ms; informational only.
- Machine evidence SHA-256:
  `e2af188f395a69df9ebfc4d3138abac995029e6bca593bab3b9117ee7a71f7b9`.

## Decision Boundary

R28 establishes a repeatable subject-evaluation protocol. It does not qualify
the baseline, approve the R27 policy, or authorize deployment. The only
authorized next step is a separately pre-registered deterministic paired
base/policy evaluation on consumed development data. Production remains on
`djimitflo:r22-e401afec`.
