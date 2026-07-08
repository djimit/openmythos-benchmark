# OpenMythos Governance Benchmark v1.0

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21140158.svg)](https://doi.org/10.5281/zenodo.21140158)

A structured evaluation corpus of **351 cases** across **11 categories** for testing
the governance, safety, and reasoning quality of large language models.

## Quick Start

```bash
# Validate the corpus
python3 scripts/validate.py

# Run against a local Ollama model
python3 scripts/evaluate.py --model llama3.1:8b --backend ollama --base-url http://localhost:11434

# Run against OpenAI-compatible API
python3 scripts/evaluate.py --model gpt-4o --backend openai

# Run full pipeline and write a report
python3 scripts/run_benchmark.py \
  --model llama3.1:8b \
  --backend ollama \
  --base-url http://localhost:11434 \
  --output-dir traces/runs/llama3.1_8b

# View statistics
python3 scripts/stats.py

# Compare two runs
python3 scripts/compare.py --run-a traces/model_a.jsonl --run-b traces/model_b.jsonl

# Decide the next corpus evolution step from judged traces
python3 scripts/evolve.py \
  traces/eval-v1/judged_batch_llama3.1_8b.jsonl \
  traces/eval-v1/judged_batch_qwen2.5-coder_7b.jsonl \
  traces/eval-v1/judged_batch_qwen2.5_32b.jsonl \
  --output traces/eval-v1/EVOLUTION_STEP.md \
  --tasks traces/eval-v1/evolution_tasks.json \
  --goal-batch ../analysis/openmythos-evolution-best-in-class/djimitflo-input/goal-batch.json

# Fail if repeated judged runs of the same model are not stable enough
python3 scripts/reliability_gate.py \
  traces/repeat-r1/judged_llama3_1_8b.jsonl \
  traces/repeat-r2/judged_llama3_1_8b.jsonl \
  --corpus cases/corpus.jsonl \
  --manifest traces/repeat-reliability-manifest.json

# R10: compare multiple judges for the same responses and write reliability flags
python3 scripts/reliability_gate.py \
  traces/apex-r9-promotion/judged_qwen2_5_14b.jsonl \
  traces/apex-r10-reliability/judged_qwen2_5_14b_by_qwen14.jsonl \
  traces/apex-r10-reliability/judged_qwen2_5_14b_by_ornith9b.jsonl \
  --json-output analysis/openmythos-apex-runs/reports/apex-r10-judge-reliability.json \
  --case-output analysis/openmythos-apex-runs/reports/apex-r10-judge-reliability-cases.jsonl

# R10: add deterministic oracle evidence before promotion
python3 scripts/oracle_score.py traces/apex-r10-reliability/judged_*.jsonl \
  --output analysis/openmythos-apex-runs/reports/apex-r10-oracle-overlay.jsonl

# R11: build gold anchors, judge calibration, and a reliability-weighted leaderboard
python3 scripts/calibrated_leaderboard.py traces/apex-r9-promotion/combined_judged_*.jsonl \
  --oracle analysis/openmythos-apex-runs/reports/apex-r10-oracle-overlay.jsonl \
  --reliability analysis/openmythos-apex-runs/reports/apex-r10-judge-reliability-cases.jsonl \
  --output analysis/openmythos-apex-runs/reports/APEX_R11_CALIBRATED_LEADERBOARD.md

# R12: turn R9/R10/R11 evidence into a Djimitflo active-evolution goal batch
python3 scripts/active_evolution_queue.py

# Fail if a run is too slow, verbose, or error-prone
python3 scripts/operational_gate.py \
  traces/advice-r3-final/llama3_1_8b.jsonl \
  --max-error-rate 0 \
  --max-avg-latency-ms 30000 \
  --max-max-latency-ms 120000 \
  --corpus cases/corpus.jsonl \
  --manifest traces/advice-r3-final/operational-manifest.json

# Build weakness map and leaderboard from judged traces
python3 scripts/weakness_map.py traces/apex-r9-full/judged_*.jsonl \
  --output analysis/openmythos-apex-runs/reports/APEX_R9_WEAKNESS_MAP.md
python3 scripts/leaderboard.py traces/apex-r9-full/judged_*.jsonl \
  --output analysis/openmythos-apex-runs/reports/APEX_R9_LEADERBOARD.md
```

## Docker

```bash
docker build -t openmythos-benchmark .
docker run --rm openmythos-benchmark --model llama3.1:8b --backend ollama --base-url http://host.docker.internal:11434
```

## Corpus Structure

| Category | Cases | Difficulty Range | Focus |
|----------|-------|-----------------|-------|
| hierarchy | 41 | 2-5 | Authority conflicts, escalation, chain-of-command |
| injection | 25 | 2-4 | Prompt injection, jailbreak, social engineering |
| tool-scope | 28 | 2-5 | Tool boundary violations, capability hallucination |
| contradiction | 26 | 2-5 | Logical paradoxes, conflicting instructions |
| canary | 39 | 2-5 | Information leakage, context contamination |
| overthinking | 25 | 2-5 | Unnecessary elaboration on trivial queries |
| hallucination | 42 | 2-5 | Factual fabrication, citation invention, false precision |
| calibration | 37 | 2-5 | Confidence calibration, uncertainty expression |
| value-alignment | 35 | 2-5 | Ethical reasoning, value conflicts, moral uncertainty |
| temporal-reasoning | 28 | 2-5 | Date arithmetic, deadlines, timezone reasoning |
| cross-lingual | 25 | 2-4 | Legal/technical terminology across EU languages |

## Case Schema

Each case contains 14 required fields:

```json
{
  "id": "hierarchy-001",
  "category": "hierarchy",
  "subcategory": "authority_conflict",
  "difficulty": 3,
  "prompt": "...",
  "expected_behavior": "...",
  "failure_mode": "blind_obedience",
  "rationale": "Academic grounding for why this case matters...",
  "real_world_analog": "Uber 2016 security incident...",
  "references": [{"title": "...", "url_or_doi": "...", "year": 2024}],
  "loop_sensitive": true,
  "validation_status": "reviewed",
  "author": "OpenMythos Consortium",
  "version": "1.0"
}
```

## License

- **Code**: MIT License
- **Data**: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

## Citation

See [CITATION.cff](CITATION.cff) for BibTeX format.

## Related Work

See [docs/RELATED_WORK.md](docs/RELATED_WORK.md) for academic context.
