# OpenMythos Apex R11 — Governance Validation Run

## Objective

Validate the moat architecture end-to-end:

1. Run the R10 governance draft cases (5 cases) against all models
2. Verify gate pipeline blocks ungoverned cloud model usage
3. Validate outcome ledger captures all outcomes
4. Confirm registry governance constraints are enforced
5. Generate promotion decision for draft cases

## Model Panel

### Governed (registry-validated)
- `qwen2.5-coder:latest` — local, commodity, tier_2_verified
- `google/gemma-4-26b-a4b-it:free` — cloud, frontier, tier_1_trusted

### Test: Governance boundary
- Attempt to run `google/gemma-4-26b-a4b-it:free` with `--data-class confidential`
- Expected: GOVERNANCE BLOCK (cloud models not allowed for confidential)

## Draft Cases

`analysis/openmythos-apex-runs/drafts/apex-r10-governance-drafts.jsonl` (5 cases):
- `contradiction-r10-001` — conflicting legal norms (difficulty 4)
- `contradiction-r10-002` — CEO vs board policy conflict (difficulty 4)
- `contradiction-r10-003` — GDPR vs national law (difficulty 4)
- `tool-scope-r10-001` — tool hallucination boundary (difficulty 3)
- `tool-scope-r10-002` — destructive operation refusal (difficulty 3)

## Commands

### Step 1: Run draft cases against local model
```bash
python3 scripts/evaluate.py \
  --corpus analysis/openmythos-apex-runs/drafts/apex-r10-governance-drafts.jsonl \
  --model qwen2.5-coder:latest --backend ollama --base-url http://localhost:11434 \
  --output traces/apex-r11/qwen2_5_coder_drafts.jsonl \
  --governance-check --data-class public --num-predict 256 --timeout 180
```

### Step 2: Run draft cases against cloud model
```bash
python3 scripts/evaluate.py \
  --corpus analysis/openmythos-apex-runs/drafts/apex-r10-governance-drafts.jsonl \
  --model google/gemma-4-26b-a4b-it:free --backend openrouter \
  --output traces/apex-r11/gemma_4_26b_drafts.jsonl \
  --governance-check --data-class public
```

### Step 3: Test governance boundary (should FAIL)
```bash
python3 scripts/evaluate.py \
  --corpus analysis/openmythos-apex-runs/drafts/apex-r10-governance-drafts.jsonl \
  --model google/gemma-4-26b-a4b-it:free --backend openrouter \
  --output traces/apex-r11/should_not_exist.jsonl \
  --governance-check --data-class confidential
# Expected: GOVERNANCE BLOCK
```

### Step 4: Judge draft cases
```bash
for model in qwen2_5_coder gemma_4_26b; do
  python3 scripts/judge.py \
    --trace traces/apex-r11/${model}_drafts.jsonl \
    --corpus analysis/openmythos-apex-runs/drafts/apex-r10-governance-drafts.jsonl \
    --judge-model qwen2.5-coder:latest --judge-backend ollama --judge-url http://localhost:11434 \
    --strict --output traces/apex-r11/judged_${model}_drafts.jsonl
done
```

### Step 5: Gate pipeline
```bash
python3 scripts/gate_pipeline.py \
  --candidate traces/apex-r11/judged_gemma_4_26b_drafts.jsonl \
  --baseline traces/apex-r11/judged_qwen2_5_coder_drafts.jsonl \
  --corpus analysis/openmythos-apex-runs/drafts/apex-r10-governance-drafts.jsonl \
  --output analysis/openmythos-apex-runs/reports/APEX_R11_GATE.md
```

### Step 6: Outcome ledger
```bash
python3 scripts/outcome_ledger.py --report
```

## Success Criteria

- [ ] Local model completes all 5 draft cases
- [ ] Cloud model completes all 5 draft cases
- [ ] Governance boundary test FAILS as expected (confidential blocked)
- [ ] Gate pipeline runs without errors
- [ ] Outcome ledger has entries for all runs
- [ ] Draft cases show discrimination (spread >= 2)

## Promotion Boundary

Draft cases can be promoted to `cases/corpus.jsonl` after:
- Spread >= 2 between models
- No all-pass or all-fail
- Governance constraints verified
