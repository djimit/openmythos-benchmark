#!/usr/bin/env python3
"""Outcome Ledger — record what happened with AI outputs, not just what was produced.

Integrates with existing trace files (traces/*.jsonl) and adds outcome metadata:
- Human review decisions
- Corrections applied
- Business outcomes
- Feedback loop to eval sets
- Audit chain for compliance

Usage:
    python3 outcome_ledger.py --record --case-id hierarchy-001 --model qwen2.5:14b --action accepted
    python3 outcome_ledger.py --record --case-id hierarchy-001 --model qwen2.5:14b --action corrected --correction citation_fix
    python3 outcome_ledger.py --report
    python3 outcome_ledger.py --feedback-loop --eval-set cases/corpus.jsonl
"""

import argparse
import hashlib
import json
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
LEDGER_PATH = REPO_ROOT / "outcomes" / "ledger.jsonl"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_outcome_id() -> str:
    return f"oc-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"


def record_outcome(
    case_id: str,
    model_id: str,
    action: str,
    correction_type: str | None = None,
    business_outcome: str | None = None,
    time_saved_minutes: float | None = None,
    error_prevented: bool | None = None,
    policy_version: str = "policy-latest",
    task_classification: str | None = None,
    notes: str | None = None,
) -> dict:
    """Record an outcome entry."""
    entry = {
        "outcome_id": make_outcome_id(),
        "timestamp": now_iso(),
        "case_id": case_id,
        "model_id": model_id,
        "action": action,  # accepted | corrected | rejected | escalated
        "correction_type": correction_type
        or "none",  # none | citation_fix | factual_error | policy_violation | rejection
        "business_outcome": business_outcome,
        "time_saved_minutes": time_saved_minutes,
        "error_prevented": error_prevented,
        "policy_version": policy_version,
        "task_classification": task_classification,
        "human_reviewed": action in ("corrected", "rejected", "accepted"),
        "feedback_incorporated": False,
        "notes": notes,
    }

    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("a") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


def load_ledger() -> list[dict]:
    """Load all ledger entries."""
    if not LEDGER_PATH.exists():
        return []
    entries = []
    with LEDGER_PATH.open() as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    return entries


def compute_kpis(entries: list[dict]) -> dict:
    """Compute outcome-based KPIs."""
    if not entries:
        return {"total": 0}

    total = len(entries)
    accepted = sum(1 for e in entries if e["action"] == "accepted")
    corrected = sum(1 for e in entries if e["action"] == "corrected")
    rejected = sum(1 for e in entries if e["action"] == "rejected")
    escalated = sum(1 for e in entries if e["action"] == "escalated")

    correction_types = defaultdict(int)
    for e in entries:
        if e["correction_type"] != "none":
            correction_types[e["correction_type"]] += 1

    time_saved = sum(e.get("time_saved_minutes") or 0 for e in entries)
    errors_prevented = sum(1 for e in entries if e.get("error_prevented"))

    # Per-model breakdown
    by_model = defaultdict(lambda: {"total": 0, "accepted": 0, "corrected": 0})
    for e in entries:
        mid = e["model_id"]
        by_model[mid]["total"] += 1
        if e["action"] == "accepted":
            by_model[mid]["accepted"] += 1
        elif e["action"] == "corrected":
            by_model[mid]["corrected"] += 1

    return {
        "total": total,
        "accepted": accepted,
        "corrected": corrected,
        "rejected": rejected,
        "escalated": escalated,
        "acceptance_rate": round(accepted / total, 3) if total else 0,
        "correction_rate": round(corrected / total, 3) if total else 0,
        "rejection_rate": round(rejected / total, 3) if total else 0,
        "escalation_rate": round(escalated / total, 3) if total else 0,
        "correction_types": dict(correction_types),
        "total_time_saved_minutes": round(time_saved, 1),
        "errors_prevented": errors_prevented,
        "by_model": {
            k: {**v, "acceptance_rate": round(v["accepted"] / v["total"], 3)}
            for k, v in by_model.items()
        },
    }


def generate_report(entries: list[dict]) -> str:
    """Generate markdown report from ledger."""
    kpis = compute_kpis(entries)
    lines = [
        "# Outcome Ledger Report",
        "",
        f"Generated: {now_iso()}",
        f"Total entries: {kpis['total']}",
        "",
        "## KPIs",
        "",
        f"| metric | value |",
        f"|--------|------:|",
        f"| Acceptance rate | {kpis.get('acceptance_rate', 0):.1%} |",
        f"| Correction rate | {kpis.get('correction_rate', 0):.1%} |",
        f"| Rejection rate | {kpis.get('rejection_rate', 0):.1%} |",
        f"| Escalation rate | {kpis.get('escalation_rate', 0):.1%} |",
        f"| Total time saved | {kpis.get('total_time_saved_minutes', 0):.0f} min |",
        f"| Errors prevented | {kpis.get('errors_prevented', 0)} |",
        "",
    ]

    if kpis.get("by_model"):
        lines.extend(
            [
                "## Per-Model Performance",
                "",
                "| model | total | accepted | acceptance rate |",
                "|-------|------:|---------:|----------------:|",
            ]
        )
        for model, stats in sorted(kpis["by_model"].items()):
            lines.append(
                f"| {model} | {stats['total']} | {stats['accepted']} | {stats['acceptance_rate']:.1%} |"
            )
        lines.append("")

    if kpis.get("correction_types"):
        lines.extend(
            [
                "## Correction Types",
                "",
                "| type | count |",
                "|------|------:|",
            ]
        )
        for ctype, count in sorted(
            kpis["correction_types"].items(), key=lambda x: -x[1]
        ):
            lines.append(f"| {ctype} | {count} |")
        lines.append("")

    return "\n".join(lines)


def feedback_loop_analysis(entries: list[dict]) -> dict:
    """Analyze which cases need eval set updates based on corrections."""
    corrections_by_case = defaultdict(list)
    for e in entries:
        if e["correction_type"] != "none":
            corrections_by_case[e["case_id"]].append(e)

    return {
        "cases_needing_eval_update": len(corrections_by_case),
        "total_corrections": sum(len(v) for v in corrections_by_case.values()),
        "top_problematic_cases": sorted(
            [(cid, len(corrs)) for cid, corrs in corrections_by_case.items()],
            key=lambda x: -x[1],
        )[:20],
    }


def demo() -> int:
    """Self-check with synthetic data."""
    # Record test outcomes
    record_outcome(
        "test-001",
        "qwen2.5:14b",
        "accepted",
        task_classification="legal_reasoning",
        time_saved_minutes=30,
    )
    record_outcome(
        "test-002",
        "qwen2.5:14b",
        "corrected",
        correction_type="citation_fix",
        task_classification="legal_reasoning",
    )
    record_outcome(
        "test-003", "llama3.1:8b", "rejected", task_classification="legal_reasoning"
    )
    record_outcome(
        "test-004",
        "qwen2.5:32b",
        "accepted",
        task_classification="governance",
        time_saved_minutes=60,
        error_prevented=True,
    )

    entries = load_ledger()
    kpis = compute_kpis(entries)

    assert kpis["total"] >= 4
    assert kpis["acceptance_rate"] > 0
    assert "qwen2.5:14b" in kpis["by_model"]

    # Test feedback loop
    fb = feedback_loop_analysis(entries)
    assert fb["total_corrections"] >= 1

    print(
        f"ledger demo OK — {kpis['total']} entries, {kpis['acceptance_rate']:.0%} acceptance"
    )

    # Clean up demo entries
    if LEDGER_PATH.exists():
        LEDGER_PATH.unlink()

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", action="store_true", help="Record an outcome")
    parser.add_argument("--case-id", type=str, help="Case identifier")
    parser.add_argument("--model", type=str, dest="model_id", help="Model identifier")
    parser.add_argument(
        "--action", type=str, choices=["accepted", "corrected", "rejected", "escalated"]
    )
    parser.add_argument(
        "--correction",
        type=str,
        dest="correction_type",
        choices=[
            "none",
            "citation_fix",
            "factual_error",
            "policy_violation",
            "rejection",
        ],
    )
    parser.add_argument(
        "--business-outcome", type=str, help="What happened in the real world"
    )
    parser.add_argument(
        "--time-saved", type=float, dest="time_saved_minutes", help="Minutes saved"
    )
    parser.add_argument(
        "--error-prevented", action="store_true", help="Whether an error was caught"
    )
    parser.add_argument("--task-classification", type=str, help="Task type")
    parser.add_argument("--notes", type=str, help="Free-form notes")
    parser.add_argument("--report", action="store_true", help="Generate report")
    parser.add_argument(
        "--feedback-loop", action="store_true", help="Analyze feedback loop"
    )
    parser.add_argument("--demo", action="store_true", help="Run self-check")
    args = parser.parse_args()

    if args.demo:
        return demo()

    if args.record:
        if not args.case_id or not args.model_id or not args.action:
            parser.error("--record requires --case-id, --model, and --action")
        entry = record_outcome(
            case_id=args.case_id,
            model_id=args.model_id,
            action=args.action,
            correction_type=args.correction_type,
            business_outcome=args.business_outcome,
            time_saved_minutes=args.time_saved_minutes,
            error_prevented=args.error_prevented,
            task_classification=args.task_classification,
            notes=args.notes,
        )
        print(json.dumps(entry, indent=2))
        return 0

    if args.report:
        entries = load_ledger()
        print(generate_report(entries))
        return 0

    if args.feedback_loop:
        entries = load_ledger()
        fb = feedback_loop_analysis(entries)
        print(json.dumps(fb, indent=2))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
