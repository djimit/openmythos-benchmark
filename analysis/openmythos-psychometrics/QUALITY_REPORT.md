# OpenMythos Psychometric Apex Quality Report

Date: 2026-07-06

Runtime:

- host: `MacBook-Pro`
- os: `Darwin`
- repo: `/Users/dlandman/OpenMythos/openmythos-benchmark`
- OpenSpec change: `openmythos-oracle-psychometric-control-plane`

## Decision

OpenMythos now has a file-based psychometric control plane:

- deterministic oracle scoring for strict-output and canary-like cases
- item-quality scoring over judged traces
- sealed split leakage guard
- R3/draft quality evidence in JSONL outputs

Best next promotion set from existing evidence:

- promote from R3 final: `overthinking-030`, `overthinking-028`, `value-alignment-033`, `value-alignment-031`, `overthinking-027`, `value-alignment-034`, `value-alignment-032`
- keep/review: `overthinking-029`
- highest-yield draft source: `value-alignment-v2`
- quarantine/rewrite cluster: `overthinking` draft cluster

## Current Baseline

Corpus baseline:

- `python3 scripts/stats.py`
  - total cases: `333`
  - categories: `11`
  - loop-sensitive: `149`
- `python3 scripts/validate.py`
  - result: pass
  - all 11 categories are present
  - all categories have at least `25` cases
- `python3 -m unittest tests/test_corpus.py`
  - result: pass
  - `11` tests passed

Methodology decision for final human gate:

- the old validator required gap-free numeric IDs per category
- evolved and promoted IDs already use historical gaps and category-prefixed variants such as `overthinking-apex-*`
- validator semantics now require unique IDs with the correct category prefix, while allowing numeric gaps after evolution rounds

R3 final quality:

- command: `python3 scripts/discrimination.py traces/advice-r3-final/judged_llama3_1_8b.jsonl traces/advice-r3-final/judged_qwen2_5_14b.jsonl traces/advice-r3-final/judged_qwen2_5_coder_7b.jsonl`
- compared cases: `8`
- discrimination: `2.625`
- dead-case rate: `0.000`
- per-category spread/dead:
  - `overthinking`: `3.50 / 0.00`
  - `value-alignment`: `3.75 / 0.00`

R3 operational gate:

- command: `python3 scripts/operational_gate.py traces/advice-r3-final/llama3_1_8b.jsonl traces/advice-r3-final/qwen2_5_14b.jsonl traces/advice-r3-final/qwen2_5_coder_7b.jsonl --max-error-rate 0 --max-avg-latency-ms 5000 --max-max-latency-ms 15000 --max-avg-tokens 250 --max-max-tokens 900`
- rows: `24`
- errors: `0`
- avg latency: `2873.0ms`
- max latency: `12125.2ms`
- avg tokens: `158.6`
- max tokens: `685`
- result: pass

## Oracle Coverage

Command:

```bash
python3 scripts/oracle_score.py \
  traces/advice-r3-final/judged_llama3_1_8b.jsonl \
  traces/advice-r3-final/judged_qwen2_5_14b.jsonl \
  traces/advice-r3-final/judged_qwen2_5_coder_7b.jsonl \
  --output analysis/openmythos-psychometrics/oracle-r3-final.jsonl
```

Result:

- rows: `24`
- oracle-applicable: `12`
- coverage: `0.500`
- oracle pass/fail: `4 / 8`
- oracle/judge disagreements: `0`
- oracle types:
  - `exact_json`: `6`
  - `exact_csv`: `3`
  - `exact_scalar`: `3`

Interpretation:

- R3 strict-output `overthinking` cases no longer require an LLM judge for pass/fail.
- The deterministic oracle agreed with the existing judge pass/fail side on all oracle-applicable R3 rows.
- This removes evaluator-bias exposure from half of R3-final judged rows.

## Item Quality

Command pattern:

```bash
python3 scripts/item_quality.py TRACE_A TRACE_B [TRACE_C] \
  --oracle-output analysis/openmythos-psychometrics/oracle-r3-final.jsonl \
  --output analysis/openmythos-psychometrics/item-quality-r3-final.jsonl
```

R3 final:

| output | cases | labels | promote |
|---|---:|---|---|
| `item-quality-r3-final.jsonl` | 8 | `promote-candidate=7`, `keep=1` | `overthinking-030`, `overthinking-028`, `value-alignment-033`, `value-alignment-031`, `overthinking-027`, `value-alignment-034`, `value-alignment-032` |

Draft clusters:

| output | cases | labels | promote |
|---|---:|---|---|
| `item-quality-canary.jsonl` | 4 | `keep=1`, `replace=3` | none |
| `item-quality-hierarchy.jsonl` | 4 | `promote-candidate=1`, `rewrite=1`, `replace=2` | `hierarchy-034` |
| `item-quality-hallucination.jsonl` | 5 | `promote-candidate=1`, `keep=1`, `replace=3` | `hallucination-029` |
| `item-quality-hall-v2.jsonl` | 4 | `promote-candidate=1`, `replace=3` | `hallucination-032` |
| `item-quality-overthinking-with-oracle.jsonl` | 5 | `replace=4`, `quarantine=1` | none |
| `item-quality-value-v1.jsonl` | 5 | `promote-candidate=1`, `rewrite=1`, `replace=3` | `value-alignment-027` |
| `item-quality-value-v2.jsonl` | 5 | `promote-candidate=4`, `replace=1` | `value-alignment-033`, `value-alignment-035`, `value-alignment-032`, `value-alignment-034` |

Cluster decision:

- `value-alignment-v2` is the only draft cluster worth mining further now.
- `overthinking` draft cluster should be quarantined as a source, not promoted as-is.
- `canary` needs a rewrite pattern; current candidates mostly do not discriminate.

## Split Safety

Manifest:

- `analysis/openmythos-psychometrics/split-manifest.json`
- contains IDs only, no prompt or response payloads
- corpus hash recorded in `split-guard-summary.json`: `f8b98965b0516e0a117740b5c5c0497c3a915e7b89d6ac3860c6a0e1a155ac8e`
- manifest hash recorded in `split-guard-summary.json`: `e1e4e31c973fdf5993fd4ba074199e8c147fe4675ed1cac4d1ba57c81d9ccf33`
- counts:
  - `train_public=4`
  - `dev_evolution=8`
  - `sealed_audit=4`

Command:

```bash
python3 scripts/split_guard.py \
  --manifest analysis/openmythos-psychometrics/split-manifest.json \
  --summary analysis/openmythos-psychometrics/split-guard-summary.json
```

Result:

- scanned paths: `3`
- scanned files: `128`
- violations: `0`
- result: pass

Calibration note:

- An earlier sealed choice using `temporal-reasoning-001` and `temporal-reasoning-002` failed because those IDs already appeared in apex artifacts.
- That failure proves the guard catches real leakage before a case is treated as sealed.

## Djimitflo Preview

Command:

```bash
npx tsx -e 'import Database from "better-sqlite3"; import { GoalBatchService } from "./packages/server/src/services/goal-batch-service"; const db=new Database("/Users/dlandman/djimitflo/.data/djimitflo.sqlite"); const svc=new GoalBatchService(db,"/Users/dlandman/openspec"); const result=svc.preview({path:"changes/openmythos-oracle-psychometric-control-plane/goal-batch.json"}); console.log(JSON.stringify(result,null,2)); db.close();'
```

Result:

- `total=4`
- `valid=4`
- `blocked=0`
- `writes=0`

No apply operation was run.

## Research Alignment

This slice follows the OpenSpec `research-basis.md`:

- HELM: keep evaluation multi-metric, not only average score.
- MT-Bench and Chatbot Arena: use LLM-as-judge, but reduce judge exposure where deterministic checks exist.
- G-Eval: LLM evaluators are useful but biased enough to need controls.
- Data-contamination research: sealed evaluation boundaries must be enforced.
- OpenAI Evals and Inspect: keep structured, reproducible eval artifacts.
- Rasch/IRT direction: separate item usefulness from model ability before scaling generation.

Engineering decision:

- Do not migrate OpenMythos to HELM, Inspect, or OpenAI Evals yet.
- The current JSONL contract is enough for this step.
- Add external framework adapters only after oracle and item-quality labels stabilize on two more evolution rounds.

## Verification

Passed:

- `python3 -m py_compile scripts/oracle_score.py scripts/item_quality.py scripts/split_guard.py`
- `python3 scripts/oracle_score.py --demo`
- `python3 scripts/item_quality.py --demo`
- `python3 scripts/split_guard.py --demo`
- `python3 scripts/reliability_gate.py --demo`
- `python3 scripts/operational_gate.py --demo`
- `python3 scripts/discrimination.py ...advice-r3-final...`
- `python3 scripts/promotion_gate.py ...advice-r3-final...`
- `python3 scripts/split_guard.py --manifest analysis/openmythos-psychometrics/split-manifest.json --summary analysis/openmythos-psychometrics/split-guard-summary.json`
- `openspec validate openmythos-oracle-psychometric-control-plane --strict`
- Djimitflo `GoalBatchService.preview`

Resolved corpus baseline:

- `python3 scripts/validate.py`
- `python3 -m unittest tests/test_corpus.py`

## Next Action

Final human gate:

- approve the validator methodology change from gap-free IDs to category-prefixed unique IDs
- approve commit scope
- approve push
