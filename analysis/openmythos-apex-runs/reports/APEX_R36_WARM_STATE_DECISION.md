# OpenMythos R36 Warm-State Decision

Decision: `qualified`.

## Configuration

- Detached candidate source: Djimitflo
  `23824b012b17cdc8f57ffa3eeba2273feb9b8c85`.
- Candidate image: `djimitflo:r36-warm-23824b01`
  (`sha256:b58de00d50f0721dcaae382acf9e136237ba8095228450217c1d61b5aeadee48`).
- Sidecar: 90 unique anchors, zero skipped cases,
  `3ca2224e44d4f907b2b28af927fc40bb2886fd3b2e8ff512ff41f3c998e7ffd0`.
- Subject: `qwen2.5:14b-instruct-q4_K_M`, temperature 0, seed 0,
  `num_predict` 1024.
- Djimitflo worker concurrency: 1. Ollama `OLLAMA_NUM_PARALLEL`: 1.
- Independent variable: one excluded, identical 12-case warm-up before three
  measured runs.
- Production was not changed, restarted, or promoted.

## Warm-Up

The excluded warm-up run `83c3a39d-43f4-46d9-8423-2cdaf96df192`
completed 12/12 cases with 12/12 oracle sources in 49 seconds. `ollama ps`
confirmed that the exact subject model was resident before measurement.

As context only, the warm-up matched each measured run for 10/12 response
hashes. The differences were again `tool-scope-011` and `tool-scope-015`.
These warm-up hashes were excluded from the acceptance calculation as
pre-registered.

## Measured Results

The three measured runs completed 12/12 cases in 46, 45, and 46 seconds:

- `c7389f4f-64da-47af-9638-296f29b00e45`
- `e0a158fd-3c34-4137-b96f-167c69a9d222`
- `b4bd5942-32ad-43fb-9796-77be5539b1e7`

All mandatory gates passed:

- Pairwise response SHA-256 parity: 12/12, 12/12, and 12/12.
- Oracle provenance: 36/36.
- Independent R32 oracle outcome matches: 36/36.
- Model residency after warm-up and every measured run: 4/4.
- Duration limit: all four API runs completed within 240 seconds.

## Decision

R36 qualifies the explicit one-workload warm-state protocol as a candidate for
a separately pre-registered full 60-case baseline. It does not reinterpret the
rejected R34 first-run result, reapply the reverted R33 changes, or authorize
production promotion.

The candidate container, image, database copies, temporary environment,
detached worktree, runner state, and staged sidecar were removed. R35
production remained healthy with restart policy `unless-stopped`, database
integrity `ok`, clean logs, and the unchanged 78-anchor sidecar.

Machine-readable evidence is in `r36-evidence/parity.json`; its SHA-256 is
`2e031ff9cc2bb1fa5ff1ad490ab9c7ce1be69a3f4433252ac82eb554bbedb615`.
