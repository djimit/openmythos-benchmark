# OpenMythos Apex R12 — Fine-Tuned Governance Model Validation

## Objective

Validate that fine-tuning on governance SFT data improves local model performance:

1. Submit fine-tuning job to cloud provider (OpenAI/Mistral)
2. Run full corpus against fine-tuned model
3. Compare R12 (fine-tuned) vs R10 (baseline) vs R9 (original)
4. Measure governance-specific improvement
5. Update outcome ledger

## Training Data

- **Source:** `analysis/openmythos-apex-runs/datasets/apex-r10-sft-gemma4.jsonl` (112 entries)
- **Holdout:** `analysis/openmythos-apex-runs/datasets/apex-r10-holdout-gemma4.jsonl` (23 entries)
- **Base model:** gpt-4o-mini (OpenAI fine-tuning) OR mistral-7b (Mistral)
- **Rationale:** Governance-specific SFT from frontier model outputs

## Fine-Tuning Options

### Option A: OpenAI Fine-Tuning (gpt-4o-mini)
- Platform: platform.openai.com/finetuning
- Cost: ~$2-5 for 112 examples, 3 epochs
- API: `POST /v1/fine_tuning/jobs`

### Option B: Mistral API (open-mistral-7b)
- Platform: console.mistral.ai
- Cost: ~$1-3
- Better for EU data residency

### Option C: Local QLoRA (workstation, 7B only)
- Requires: pip install torch transformers peft trl
- Base: qwen2.5-coder:7b (fits in 8GB with QLoRA 4-bit)
- Time: ~2-4 hours on RTX 2060 SUPER

## Commands

### Step 1: Prepare training data (OpenAI format)
```bash
python3 scripts/prepare_openai_ft.py \
  --input analysis/openmythos-apex-runs/datasets/apex-r10-sft-gemma4.jsonl \
  --output analysis/openmythos-apex-runs/datasets/r12-openai-ft.jsonl \
  --format chat
```

### Step 2: Submit fine-tuning job
```bash
# OpenAI
openai fine_tuning jobs create \
  --training_file analysis/openmythos-apex-runs/datasets/r12-openai-ft.jsonl \
  --model gpt-4o-mini-2024-07-18 \
  --suffix "openmythos-governance-r12"
```

### Step 3: Run evaluation (after fine-tuning completes)
```bash
python3 scripts/evaluate.py \
  --corpus cases/corpus.jsonl \
  --model ft:gpt-4o-mini-2024-07-18:personal:openmythos-governance-r12:XXXXX \
  --backend openai \
  --output traces/apex-r12/ft_gpt_4o_mini.jsonl \
  --governance-check --data-class public
```

### Step 4: Judge + Leaderboard
```bash
python3 scripts/judge.py \
  --trace traces/apex-r12/ft_gpt_4o_mini.jsonl \
  --corpus cases/corpus.jsonl \
  --judge-model qwen2.5-coder:latest \
  --judge-backend ollama --judge-url http://localhost:11434 \
  --strict --output traces/apex-r12/judged_ft_gpt_4o_mini.jsonl

python3 scripts/leaderboard.py \
  traces/apex-r9-full/judged_qwen2_5_coder_7b.jsonl \
  traces/apex-r10-governance/judged_gemma_4_26b.jsonl \
  traces/apex-r12/judged_ft_gpt_4o_mini.jsonl \
  --output analysis/openmythos-apex-runs/reports/APEX_R12_LEADERBOARD.md \
  --json-output analysis/openmythos-apex-runs/reports/apex-r12-leaderboard.json
```

## Success Criteria

- [ ] Fine-tuning job completes successfully
- [ ] R12 model scores > R10 baseline on governance categories
- [ ] Improvement visible in: contradiction, hierarchy, tool-scope
- [ ] No regression on other categories
- [ ] Cost < $10 total

## Expected Outcome

If fine-tuning works:
- Governance-specific categories improve 20-40%
- Overall score approaches cloud frontier model
- Latency stays low (local inference possible if using 7B)
- Cost per outcome drops vs pure cloud approach
