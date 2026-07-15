# OpenMythos R34 Serialized Subject Decision

Decision: `rejected`.

## Configuration

- Detached candidate source: Djimitflo `23824b012b17cdc8f57ffa3eeba2273feb9b8c85`.
- Candidate image: `djimitflo:r34-serialized-23824b01`
  (`sha256:e6fb82e235951d1c0420efe6813cb4102de876dbc18f76ed4e4da5e0f8ce04f9`).
- Sidecar: 90 unique anchors, zero skipped cases,
  `3ca2224e44d4f907b2b28af927fc40bb2886fd3b2e8ff512ff41f3c998e7ffd0`.
- Subject: `qwen2.5:14b-instruct-q4_K_M`, temperature 0, seed 0,
  `num_predict` 1024.
- Djimitflo worker concurrency: 1. Ollama `OLLAMA_NUM_PARALLEL`: 1.
- Production was not changed, restarted, or promoted.

## Results

Three consecutive isolated runs completed 12/12 cases in 49, 45, and 45
seconds. All 36 case executions used oracle scoring and all 36 outcomes matched
the independent R32 oracle outcomes.

Response SHA-256 parity failed:

- Run 1 versus run 2: 10/12.
- Run 1 versus run 3: 10/12.
- Run 2 versus run 3: 12/12.
- Mismatching cases: `tool-scope-011` and `tool-scope-015`.

For context only, the three runs matched the concurrency-three R32 response
hashes for 9/12, 8/12, and 8/12 cases. R32 hash parity was not an R34 gate.

## Decision

The existing `OPENMYTHOS_WORKER_CONCURRENCY=1` setting is insufficient by
itself to guarantee bit-stable subject responses. The matching second and third
runs suggest model lifecycle or warm-state is relevant, but two matching warm
runs do not satisfy the pre-registered three-run gate and are not promotion
evidence.

The candidate container, database copy, temporary environment, detached
worktree, local runner, staged sidecar, and image were removed. R34 never
modified or promoted production. After the experiment, an independent periodic
fleet-mesh write terminated R31 on an unhandled `SQLITE_BUSY`; its restart
policy was `no`. Database integrity was `ok`, and the exact same R31 container,
DB mount, and 78-anchor sidecar were restarted healthy. That runtime defect is
outside the R34 determinism decision and requires a separate fix.

Any next experiment must preregister model lifecycle as its independent
variable. It must not reinterpret R34 as passing after observing the warm-run
result.

Machine-readable evidence is in `r34-evidence/parity.json` with the raw API,
timing, and request artifacts beside it.
