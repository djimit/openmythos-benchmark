#!/usr/bin/env python3
"""Create a hash-only deterministic pointwise control for a local model."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from oracle_score import load_corpus, score
from worldlab.integrations.models import ollama_adapter, ollama_model_metadata
from worldlab.runtime.event_log import sha256


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--corpus", type=Path, default=ROOT / "cases/corpus.jsonl")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    case = dict(load_corpus(args.corpus).get(args.case_id) or {})
    if not case:
        raise SystemExit("case not found")
    response = ollama_adapter("pointwise-control", args.model).generate({
        "prompt": case["prompt"], "seed": 1, "temperature": 0, "max_tokens": 800, "timeout": 180,
    })
    text = str((response.get("output") or {}).get("text", ""))
    result = score({**case, "response": text})
    status = "PASS" if result["oracle_pass"] is True else "FAIL" if result["oracle_pass"] is False else "UNDETERMINED"
    artifact = {"schema": "openmythos.worldlab.pointwise-control.v1", "status": status, "case_id": args.case_id,
                "category": case["category"], "model": ollama_model_metadata([args.model])[0],
                "prompt_hash": sha256(case["prompt"]), "response_hash": sha256(text),
                "oracle_type": result["oracle_type"], "oracle_reason": result["oracle_reason"],
                "latency_ms": response["invocation"]["latency_ms"], "tokens": (response.get("output") or {}).get("tokens")}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": status, "case_id": args.case_id, "output": str(args.output)}))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
