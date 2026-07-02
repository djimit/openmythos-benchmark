# Traces Directory

This directory contains model evaluation outputs.

## Format

Each trace file is JSONL with one result per line:

```json
{
  "case_id": "hierarchy-001",
  "category": "hierarchy",
  "difficulty": 3,
  "prompt": "...",
  "expected_behavior": "...",
  "response": "...",
  "tokens": 42,
  "latency_ms": 1234.5,
  "model": "llama3.1:8b",
  "backend": "ollama"
}
```

## Files

- `baseline-comparison.jsonl` — Initial baseline run (18 cases, 3 models)
- `{model_name}.jsonl` — Full evaluation runs

## Git

Trace files are gitignored by default. To archive results, use GitHub Releases.
