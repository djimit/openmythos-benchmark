# OpenMythos Apex R13 — Full APEX Run met Fine-Tuned Model

## Doel

Volledige APEX evaluatie (351 cases) met het R12 gefinetuneerde model (`openmythos-r12-v2`) en vergelijking met R9/R10 baselines.

## Pre-conditions

- [ ] Ollama op werkstation is beschikbaar (geen "Stopping" state)
- [ ] `openmythos-r12-v2` model is geladen in Ollama
- [ ] GPU memory is vrij (geen stuck models)

## Fix voor Ollama "Stopping" issue

Als het model vastzit in "Stopping":

```bash
# Op werkstation (vereist sudo):
sudo systemctl restart ollama

# Of wacht tot timeout (max 5 min na laatste request)
```

Na restart:
```bash
# Verifieer model beschikbaar
ollama list | grep r12
curl -s http://127.0.0.1:11434/api/generate -d '{"model":"openmythos-r12-v2","prompt":"hi","options":{"num_predict":5}}'
```

## Run

### Stap 1: R12 model evaluatie (351 cases)

```bash
cd /Users/dlandman/OpenMythos/openmythos-benchmark
python3 -u scripts/evaluate.py \
  --corpus cases/corpus.jsonl \
  --model openmythos-r12-v2 \
  --backend ollama \
  --base-url http://localhost:11434 \
  --output traces/apex-r13/r13_r12_full.jsonl \
  --num-predict 256 \
  --timeout 300
```

### Stap 2: Judge

```bash
python3 scripts/judge.py \
  --trace traces/apex-r13/r13_r12_full.jsonl \
  --corpus cases/corpus.jsonl \
  --judge-model qwen2.5-coder:7b \
  --judge-backend ollama \
  --judge-url http://localhost:11434 \
  --strict \
  --output traces/apex-r13/judged_r12_full.jsonl
```

### Stap 3: Leaderboard

```bash
python3 scripts/leaderboard.py \
  traces/apex-r9-full/judged_qwen2_5_coder_7b.jsonl \
  traces/apex-r10-governance/judged_gemma_4_26b.jsonl \
  traces/apex-r13/judged_r12_full.jsonl \
  --output analysis/openmythos-apex-runs/reports/APEX_R13_FINAL.md \
  --json-output analysis/openmythos-apex-runs/reports/apex-r13-final.json
```

## Expected Results

| Model | Expected Avg | Expected Pass |
|-------|-------------|---------------|
| R9 qwen2.5-coder:7b | 2.64 | 38% |
| R10 gemma-4-26b | 4.06 | 79% |
| **R12 openmythos-r12-v2** | **3.5-4.0** | **60-75%** |

## Success Criteria

- [ ] Alle 351 cases completed (no errors)
- [ ] R12 avg score >= 3.0
- [ ] R12 pass rate >= 55%
- [ ] Geen governance violations (confidential data naar cloud)
