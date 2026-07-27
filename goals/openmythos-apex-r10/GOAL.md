# OpenMythos Apex R10 Goal — Governance Integration Run

## Objective

Execute the first governance-integrated benchmark run:

1. Run the full 351-case corpus against the expanded R10 model panel (local + cloud)
2. Validate model registry governance constraints (data class, pool, lifecycle)
3. Record outcomes in the Outcome Ledger for all runs
4. Generate weakness map + leaderboard with governance metadata
5. Test the gate pipeline end-to-end

## Model Panel

### Local (private-hosted)
- `qwen2.5-coder:7b` — commodity tier, tier_2_verified
- `llama3.1:8b` — commodity tier, tier_1_trusted
- `qwen2.5:14b-instruct-q4_K_M` — differentiated tier, tier_2_verified

### Cloud (hosted, governance-filtered)
- `qwen/qwen3-coder-480b` — differentiated, tier_2_verified, free
- `deepseek/deepseek-v4-flash` — differentiated, tier_2_verified, free
- `openai/gpt-oss-120b` — differentiated, tier_1_trusted, free

### Judge
- `qwen2.5:32b-instruct-q4_K_M` (local, consistent with R9)

## Governance Constraints

- Cloud models: `allowed_data_classes = [public, internal]` only
- No cloud model processes `confidential` or `restricted` data
- All models must have `lifecycle_state = production` in registry
- All models must have `security_status = scanned`
- Sovereign fallback: if cloud APIs fail, route to local models

## Commands

### Step 1: Validate registry before run
```bash
python3 scripts/model_registry.py --validate
python3 scripts/model_registry.py --list
```

### Step 2: Run local models (werkstation)
```bash
python3 scripts/evaluate.py --corpus cases/corpus.jsonl --model qwen2.5-coder:7b --backend ollama --base-url http://192.168.1.28:11434 --output traces/apex-r10-governance/qwen2_5_coder_7b.jsonl --resume --num-predict 256 --timeout 180
python3 scripts/evaluate.py --corpus cases/corpus.jsonl --model llama3.1:8b --backend ollama --base-url http://192.168.1.28:11434 --output traces/apex-r10-governance/llama3_1_8b.jsonl --resume --num-predict 256 --timeout 180
python3 scripts/evaluate.py --corpus cases/corpus.jsonl --model qwen2.5:14b-instruct-q4_K_M --backend ollama --base-url http://192.168.1.28:11434 --output traces/apex-r10-governance/qwen2_5_14b.jsonl --resume --num-predict 256 --timeout 180
```

### Step 3: Run cloud models (via OpenRouter)
```bash
python3 scripts/evaluate.py --corpus cases/corpus.jsonl --model qwen/qwen3-coder-480b --backend openrouter --output traces/apex-r10-governance/qwen3_coder_480b.jsonl --resume --num-predict 256 --timeout 180
python3 scripts/evaluate.py --corpus cases/corpus.jsonl --model deepseek/deepseek-v4-flash --backend openrouter --output traces/apex-r10-governance/deepseek_v4_flash.jsonl --resume --num-predict 256 --timeout 180
python3 scripts/evaluate.py --corpus cases/corpus.jsonl --model openai/gpt-oss-120b --backend openrouter --output traces/apex-r10-governance/gpt_oss_120b.jsonl --resume --num-predict 256 --timeout 180
```

### Step 4: Judge all traces
```bash
for model in qwen2_5_coder_7b llama3_1_8b qwen2_5_14b qwen3_coder_480b deepseek_v4_flash gpt_oss_120b; do
  python3 scripts/judge.py --trace traces/apex-r10-governance/${model}.jsonl --corpus cases/corpus.jsonl --judge-model qwen2.5:32b-instruct-q4_K_M --judge-backend ollama --judge-url http://192.168.1.28:11434 --strict --output traces/apex-r10-governance/judged_${model}.jsonl --resume
done
```

### Step 5: Gate pipeline
```bash
python3 scripts/gate_pipeline.py \
  --candidate traces/apex-r10-governance/judged_qwen3_coder_480b.jsonl traces/apex-r10-governance/judged_deepseek_v4_flash.jsonl traces/apex-r10-governance/judged_gpt_oss_120b.jsonl \
  --baseline traces/apex-r9-full/judged_qwen2_5_coder_7b.jsonl traces/apex-r9-full/judged_llama3_1_8b.jsonl traces/apex-r9-full/judged_qwen2_5_14b.jsonl \
  --corpus cases/corpus.jsonl \
  --output analysis/openmythos-apex-runs/reports/APEX_R10_GATE_PIPELINE.md
```

### Step 6: Reports
```bash
python3 scripts/weakness_map.py traces/apex-r10-governance/judged_*.jsonl --output analysis/openmythos-apex-runs/reports/APEX_R10_WEAKNESS_MAP.md --json-output analysis/openmythos-apex-runs/reports/apex-r10-weakness-map.json
python3 scripts/leaderboard.py traces/apex-r10-governance/judged_*.jsonl --output analysis/openmythos-apex-runs/reports/APEX_R10_LEADERBOARD.md --json-output analysis/openmythos-apex-runs/reports/apex-r10-leaderboard.json
```

### Step 7: Outcome Ledger
```bash
python3 scripts/outcome_ledger.py --report
```

## Promotion Boundary

R10 does not mutate `cases/corpus.jsonl`. Draft cases can only be promoted after:
- Gate pipeline passes (operational + regression + promotion)
- Governance constraints verified for all models
- Outcome ledger shows acceptance rate > 50% for new cloud models

## Success Criteria

- [ ] All 6 models complete full corpus run
- [ ] Registry validates without errors
- [ ] Gate pipeline passes for cloud models vs R9 baseline
- [ ] Weakness map shows category coverage
- [ ] Outcome ledger has entries for all runs
- [ ] No confidential data sent to cloud models (verified by governance filter)
