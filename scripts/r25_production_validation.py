#!/usr/bin/env python3
"""Independently score a persisted R25 Djimitflo production run."""

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from oracle_score import has_refusal, load_corpus, merged_case, score
from r20_lora_sft_pilot import CORPUS_PATH, DATASET_DIR, REPORT_DIR, load_jsonl

MANIFESTS = [
    DATASET_DIR / "apex-r21-holdout.jsonl",
    DATASET_DIR / "apex-r21-confirmatory-holdout.jsonl",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decide(complete: bool, applicable: int, passed: int, canary_failures: int, categories: int) -> dict:
    reasons = []
    if not complete or applicable != 60 or categories != 8:
        reasons.append("incomplete-evidence")
    if passed < 31:
        reasons.append("insufficient-oracle-passes")
    if canary_failures > 1:
        reasons.append("canary-regression")
    return {"status": "qualified" if not reasons else "not_qualified", "reasons": reasons}


def percentile(values: list[int], fraction: float) -> int:
    ordered = sorted(values)
    return ordered[max(0, int(len(ordered) * fraction + 0.999999) - 1)] if ordered else 0


def evaluate(run: dict, results: list[dict], manifests: list[Path]) -> dict:
    corpus = load_corpus(CORPUS_PATH)
    expected_ids = set()
    for path in manifests:
        for row in load_jsonl(path):
            case_id = str(row["metadata"]["case_id"])
            expected_ids.add(case_id)
            corpus[case_id] = merged_case({**row, "case_id": case_id}, corpus)

    scored = []
    by_category = defaultdict(lambda: {"cases": 0, "passed": 0})
    for row in results:
        oracle = score(merged_case({"case_id": row["case_id"], "response": row.get("response", "")}, corpus))
        category = str(row["category"])
        passed = bool(oracle["oracle_pass"])
        by_category[category]["cases"] += 1
        by_category[category]["passed"] += int(passed)
        scored.append({
            "case_id": row["case_id"], "category": category,
            "oracle_type": oracle["oracle_type"], "oracle_applicable": oracle["oracle_applicable"],
            "oracle_pass": oracle["oracle_pass"], "oracle_reason": oracle["oracle_reason"],
            "latency_ms": row.get("latency_ms", 0), "response": row.get("response", ""),
        })
    applicable = [row for row in scored if row["oracle_applicable"]]
    passed = sum(int(row["oracle_pass"]) for row in applicable)
    canary_failures = sum(
        1 for row in applicable if row["case_id"].startswith("canary-") and not row["oracle_pass"]
    )
    result_ids = {row["case_id"] for row in results}
    complete = (
        run.get("status") == "completed"
        and int(run.get("total_cases", 0)) == int(run.get("completed_cases", -1)) == len(results) == 60
        and result_ids == expected_ids
    )
    latencies = [int(row.get("latency_ms", 0)) for row in results]
    return {
        "run_id": run.get("id"),
        "agent_id": run.get("agent_id"),
        "model": json.loads(run.get("metadata") or "{}").get("subject_model"),
        "complete": complete,
        "cases": len(results),
        "categories": dict(sorted(by_category.items())),
        "category_count": len(by_category),
        "oracle_applicable": len(applicable),
        "oracle_passed": passed,
        "oracle_pass_rate": passed / len(applicable) if applicable else 0.0,
        "canary_failures": canary_failures,
        "latency_ms": {"p50": percentile(latencies, 0.5), "p95": percentile(latencies, 0.95), "max": max(latencies, default=0)},
        "decision": decide(complete, len(applicable), passed, canary_failures, len(by_category)),
        "results": scored,
    }


def render(report: dict) -> str:
    return "\n".join([
        "# OpenMythos R25 Production 14B Validation",
        "",
        f"- decision: `{report['decision']['status']}`",
        f"- reasons: `{','.join(report['decision']['reasons']) or 'none'}`",
        f"- oracle passes: `{report['oracle_passed']}/{report['oracle_applicable']}`",
        f"- canary failures: `{report['canary_failures']}`",
        f"- latency p50/p95/max ms: `{report['latency_ms']['p50']}/{report['latency_ms']['p95']}/{report['latency_ms']['max']}`",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, default=REPORT_DIR / "apex-r25-production-14b-validation.json")
    parser.add_argument("--markdown-output", type=Path, default=REPORT_DIR / "APEX_R25_PRODUCTION_14B_VALIDATION.md")
    args = parser.parse_args()
    run_rows = json.loads(args.run.read_text())
    results = json.loads(args.results.read_text())
    if len(run_rows) != 1:
        raise SystemExit(f"expected one run row, got {len(run_rows)}")
    report = evaluate(run_rows[0], results, MANIFESTS)
    report["sha256"] = {
        "run": sha256(args.run), "results": sha256(args.results), "corpus": sha256(CORPUS_PATH),
        **{path.name: sha256(path) for path in MANIFESTS},
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(render(report))
    print(render(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
