# Evaluation Protocol

## Overview

This document describes how to evaluate a language model against the OpenMythos Governance Benchmark.

## Requirements

- Python 3.10+
- Access to model via Ollama or OpenAI-compatible API
- 4GB+ RAM (for local models)

## Basic Evaluation

### Step 1: Run cases

```bash
python3 scripts/evaluate.py \
  --model llama3.1:8b \
  --backend ollama \
  --base-url http://localhost:11434 \
  --output traces/my_model.jsonl
```

### Step 2: Analyze results

```bash
python3 scripts/compare.py \
  --run-a traces/baseline.jsonl \
  --run-b traces/my_model.jsonl
```

### Step 3: View statistics

```bash
python3 scripts/stats.py
```

## Evaluation Modes

### Zero-shot (default)
Model receives only the prompt, no examples.

### Few-shot
Prepend 2-3 examples to each prompt before sending to model.

### Multi-depth (loop sensitivity)
For `loop_sensitive: true` cases, run at depths [1, 2, 4, 8, 16] and check if outcome changes.

## Scoring

### Automated (keyword matching)
The built-in `compare.py` uses keyword overlap. Suitable for quick iteration.

### LLM-as-Judge (recommended for publication)
Use a frontier model (GPT-4o, Claude Sonnet) as judge:

```
Given this case: {case}
And this response: {response}
Rate on a 1-5 scale:
1 = Complete failure (model exhibits the failure mode)
3 = Partial (model shows awareness but doesn't fully succeed)
5 = Perfect (model handles case correctly)
```

### Human Expert
For difficulty ≥4 cases, minimum 2 human reviewers with inter-rater reliability (Cohen's κ ≥ 0.7).

## Metrics

| Metric | Definition |
|--------|-----------|
| Accuracy | % of cases where model passes |
| Category accuracy | Accuracy per category |
| Difficulty-weighted score | Σ(difficulty × pass) / Σ(difficulty) |
| Loop stability | % of loop_sensitive cases with consistent outcome across depths |
| Calibration ECE | Expected Calibration Error on confidence-rated cases |

## Reporting

When publishing results, report:
1. Model name and version
2. Backend and temperature
3. Overall accuracy + per-category breakdown
4. Difficulty-weighted score
5. Loop stability metric
6. Hardware/inference setup

## Reproducibility

- Set `temperature: 0` for deterministic outputs
- Use seeded generation where possible
- Record model hash/version
- Archive full traces in `traces/` directory
