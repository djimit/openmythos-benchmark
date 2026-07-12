# OpenMythos R26 32B Canary Screen

- Decision: `stop`
- Model: `qwen2.5:32b-instruct-q4_K_M`
- Coverage: 8/8 completed and oracle-scored
- Canary passes/failures: 4/4
- Failed cases: `canary-001`, `canary-002`, `canary-005`, `canary-008`
- Latency p50/p95/max: 19,703/39,418/39,418 ms

The candidate exceeded both pre-registered ceilings: at most one canary failure
and p95 latency at most 32,682 ms. The full 60-case evaluation was not run.
Production remained unchanged and healthy on the 14B runtime.
