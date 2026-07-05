# OpenMythos Governance Benchmark v1.0

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21140158.svg)](https://doi.org/10.5281/zenodo.21140158)

A structured evaluation corpus of **275 cases** across **11 categories** for testing
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
```

## Docker

```bash
docker build -t openmythos-benchmark .
docker run --rm openmythos-benchmark --model llama3.1:8b --backend ollama --base-url http://host.docker.internal:11434
```

## Corpus Structure

| Category | Cases | Difficulty Range | Focus |
|----------|-------|-----------------|-------|
| hierarchy | 25 | 2-5 | Authority conflicts, escalation, chain-of-command |
| injection | 25 | 2-4 | Prompt injection, jailbreak, social engineering |
| tool-scope | 25 | 1-4 | Tool boundary violations, capability hallucination |
| contradiction | 25 | 1-4 | Logical paradoxes, conflicting instructions |
| canary | 25 | 1-4 | Information leakage, context contamination |
| overthinking | 25 | 1-3 | Unnecessary elaboration on trivial queries |
| hallucination | 25 | 2-5 | Factual fabrication, citation invention, false precision |
| calibration | 25 | 1-5 | Confidence calibration, uncertainty expression |
| value-alignment | 25 | 2-5 | Ethical reasoning, value conflicts, moral uncertainty |
| temporal-reasoning | 25 | 2-4 | Date arithmetic, deadlines, timezone reasoning |
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
