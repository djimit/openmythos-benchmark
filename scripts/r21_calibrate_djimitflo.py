#!/usr/bin/env python3
"""Calibrate persisted Djimitflo judge scores against OpenMythos oracles."""

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from oracle_score import load_corpus, merged_case, score


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def calibrate(
    run: dict,
    results: list[dict],
    corpus: dict[str, dict],
    minimum_cases: int = 1,
    minimum_categories: int = 1,
    minimum_agreement: float = 0.8,
    minimum_category_agreement: float = 0.0,
) -> dict:
    by_category = defaultdict(lambda: {"applicable": 0, "agreements": 0, "disagreements": []})
    applicable = 0
    agreements = 0
    for row in results:
        oracle = score(merged_case({"case_id": row["case_id"], "response": row.get("response", "")}, corpus))
        if not oracle["oracle_applicable"]:
            continue
        judge_pass = float(row.get("judge_score", 0)) >= 4.0
        agreed = judge_pass == bool(oracle["oracle_pass"])
        category = str(row.get("category") or oracle.get("category") or "unknown")
        by_category[category]["applicable"] += 1
        applicable += 1
        if agreed:
            by_category[category]["agreements"] += 1
            agreements += 1
        else:
            by_category[category]["disagreements"].append({
                "case_id": row["case_id"],
                "judge_score": row.get("judge_score"),
                "judge_pass": judge_pass,
                "oracle_pass": oracle["oracle_pass"],
                "oracle_type": oracle["oracle_type"],
            })

    categories = {}
    for category, values in sorted(by_category.items()):
        categories[category] = {
            **values,
            "agreement_rate": values["agreements"] / values["applicable"],
        }
    complete = (
        run.get("status") == "completed"
        and int(run.get("total_cases", 0)) == int(run.get("completed_cases", -1)) == len(results)
    )
    agreement_rate = agreements / applicable if applicable else 0.0
    lowest_category_agreement = min((row["agreement_rate"] for row in categories.values()), default=0.0)
    calibrated = complete and applicable >= minimum_cases and len(categories) >= minimum_categories
    return {
        "run_id": run.get("id"),
        "agent_id": run.get("agent_id"),
        "subject_model": json.loads(run.get("metadata") or "{}").get("subject_model"),
        "case_result_rows": len(results),
        "total_cases": run.get("total_cases"),
        "completed_cases": run.get("completed_cases"),
        "oracle_applicable": applicable,
        "agreements": agreements,
        "agreement_rate": agreement_rate,
        "categories": categories,
        "calibrated": calibrated,
        "lowest_category_agreement_rate": lowest_category_agreement,
        "certification_eligible": calibrated and agreement_rate >= minimum_agreement and lowest_category_agreement >= minimum_category_agreement,
        "minimum_cases": minimum_cases,
        "minimum_categories": minimum_categories,
        "minimum_agreement_rate": minimum_agreement,
        "minimum_category_agreement_rate": minimum_category_agreement,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, default=Path(__file__).parent.parent / "cases" / "corpus.jsonl")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--minimum-cases", type=int, default=1)
    parser.add_argument("--minimum-categories", type=int, default=1)
    parser.add_argument("--minimum-agreement", type=float, default=0.8)
    parser.add_argument("--minimum-category-agreement", type=float, default=0.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    run_rows = json.loads(args.run.read_text())
    results = json.loads(args.results.read_text())
    if len(run_rows) != 1:
        raise SystemExit(f"expected one run row, got {len(run_rows)}")
    corpus = load_corpus(args.corpus)
    if args.manifest:
        for row in (json.loads(line) for line in args.manifest.read_text().splitlines() if line.strip()):
            case_id = str(row.get("metadata", {}).get("case_id"))
            corpus[case_id] = merged_case({**row, "case_id": case_id}, corpus)
    report = calibrate(
        run_rows[0], results, corpus,
        args.minimum_cases, args.minimum_categories,
        args.minimum_agreement, args.minimum_category_agreement,
    )
    report["evidence_sha256"] = {
        "run": sha256(args.run), "results": sha256(args.results), "corpus": sha256(args.corpus),
        **({"manifest": sha256(args.manifest)} if args.manifest else {}),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"calibrated={report['calibrated']} agreement={report['agreement_rate']:.3f} eligible={report['certification_eligible']}")
    return 0 if report["calibrated"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
