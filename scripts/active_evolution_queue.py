#!/usr/bin/env python3
"""Build a Djimitflo-ready active evolution queue from OpenMythos evidence."""

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
REPORT_DIR = REPO_ROOT / "analysis" / "openmythos-apex-runs" / "reports"


def load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing required report: {path}")
    return json.loads(path.read_text())


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"missing required report: {path}")
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def mean(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def round3(value: float) -> float:
    return round(float(value), 3)


def by_category(rows: list[dict]) -> dict[str, dict]:
    return {row["category"]: row for row in rows}


def anchor_summary(anchors: list[dict]) -> dict[str, dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in anchors:
        grouped[row.get("category", "unknown")].append(row)
    out = {}
    for category, rows in grouped.items():
        oracle_types = sorted({str(row.get("oracle_type", "unknown")) for row in rows})
        out[category] = {
            "anchors": len(rows),
            "agreement_rate": round3(mean(1.0 if row.get("judge_agrees") else 0.0 for row in rows)),
            "disagreements": sum(1 for row in rows if not row.get("judge_agrees")),
            "oracle_types": oracle_types,
        }
    return out


def calibration_summary(calibrated: dict) -> dict[str, dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in calibrated.get("calibration", {}).get("categories", []):
        grouped[row.get("category", "unknown")].append(row)
    out = {}
    for category, rows in grouped.items():
        agreements = [float(row.get("agreement_rate", 0.0)) for row in rows]
        false_pass = [float(row.get("false_pass_rate", 0.0)) for row in rows]
        false_fail = [float(row.get("false_fail_rate", 0.0)) for row in rows]
        bias = [abs(float(row.get("strictness_bias", 0.0))) for row in rows]
        weights = [float(row.get("weight", 0.0)) for row in rows]
        out[category] = {
            "judges": len(rows),
            "min_agreement_rate": round3(min(agreements) if agreements else 0.0),
            "avg_agreement_rate": round3(mean(agreements)),
            "max_false_pass_rate": round3(max(false_pass) if false_pass else 0.0),
            "max_false_fail_rate": round3(max(false_fail) if false_fail else 0.0),
            "max_abs_bias": round3(max(bias) if bias else 0.0),
            "min_weight": round3(min(weights) if weights else 0.0),
        }
    return out


def category_priorities(
    weakness: dict,
    reliability: dict,
    promotion: dict,
    calibrated: dict,
    anchors: list[dict],
    min_anchor_count: int,
) -> list[dict]:
    weakness_by_cat = by_category(weakness.get("categories", []))
    reliability_by_cat = by_category(reliability.get("categories", []))
    promotion_by_cat = promotion.get("categories", {})
    anchors_by_cat = anchor_summary(anchors)
    calibration_by_cat = calibration_summary(calibrated)
    categories = sorted(
        set(weakness_by_cat)
        | set(reliability_by_cat)
        | set(promotion_by_cat)
        | set(anchors_by_cat)
        | set(calibration_by_cat)
    )
    rows = []
    for category in categories:
        weakness_row = weakness_by_cat.get(category, {})
        reliability_row = reliability_by_cat.get(category, {})
        promotion_row = promotion_by_cat.get(category, {})
        anchor_row = anchors_by_cat.get(category, {"anchors": 0, "agreement_rate": 0.0, "disagreements": 0})
        calibration_row = calibration_by_cat.get(category, {})

        weakness_score = float(weakness_row.get("weakness", 0.0))
        instability_rate = float(reliability_row.get("instability_rate", 0.0))
        promotion_dead_rate = float(promotion_row.get("dead_rate", weakness_row.get("dead_rate", 0.0)))
        anchor_count = int(anchor_row.get("anchors", 0))
        oracle_gap = max(0.0, (min_anchor_count - anchor_count) / min_anchor_count)
        min_agreement = float(calibration_row.get("min_agreement_rate", anchor_row.get("agreement_rate", 0.0)))
        calibration_gap = 1.0 if anchor_count == 0 else max(0.0, 0.75 - min_agreement)

        priority = (
            weakness_score * 2.0
            + instability_rate * 3.0
            + oracle_gap * 1.25
            + calibration_gap
            + promotion_dead_rate * 0.75
        )
        drivers = []
        if instability_rate >= 0.5:
            drivers.append("judge-instability")
        if oracle_gap > 0:
            drivers.append("oracle-gap")
        if weakness_score >= 1.0:
            drivers.append("weak-category")
        if promotion_dead_rate >= 0.25:
            drivers.append("dead-or-nondiscriminating-cases")
        if calibration_gap > 0.25:
            drivers.append("calibration-gap")

        rows.append(
            {
                "category": category,
                "priority": round3(priority),
                "drivers": drivers,
                "weakness": round3(weakness_score),
                "instability_rate": round3(instability_rate),
                "promotion_dead_rate": round3(promotion_dead_rate),
                "anchor_count": anchor_count,
                "oracle_gap": round3(oracle_gap),
                "min_calibration_agreement": round3(min_agreement),
                "calibration_gap": round3(calibration_gap),
                "avg_spread": round3(float(weakness_row.get("avg_spread", 0.0))),
                "cases": int(weakness_row.get("cases", reliability_row.get("cases", 0))),
            }
        )
    return sorted(rows, key=lambda row: (-row["priority"], row["category"]))


def top_categories(rows: list[dict], driver: str, limit: int = 3) -> list[str]:
    return [row["category"] for row in rows if driver in row["drivers"]][:limit]


def top_dead_cases(weakness: dict, priority_categories: list[str], limit: int = 12) -> list[str]:
    cases = list(enumerate(weakness.get("cases", [])))
    priority_rank = {category: idx for idx, category in enumerate(priority_categories)}
    ranked = [
        (idx, row)
        for idx, row in cases
        if row.get("dead") or int(row.get("spread", 0)) < 2 or row.get("all_pass") or row.get("all_fail")
    ]
    scoped = [(idx, row) for idx, row in ranked if row.get("category") in priority_rank]
    selected = scoped or ranked
    selected = sorted(
        selected,
        key=lambda item: (
            priority_rank.get(item[1].get("category"), len(priority_rank)),
            item[0],
        ),
    )
    return [row["case_id"] for _, row in selected[:limit]]


def build_goals(report: dict) -> list[dict]:
    categories = report["category_priorities"]
    instability = top_categories(categories, "judge-instability")
    oracle_gap = top_categories(categories, "oracle-gap", 4)
    weak = top_categories(categories, "weak-category", 4)
    dead_cases = report["dead_or_low_spread_cases"][:8]

    return [
        {
            "key": "om-r12-01-stabilize-low-reliability-categories",
            "title": "Stabilize low-reliability judge categories",
            "risk": "medium",
            "target": "openmythos-benchmark/scripts/reliability_gate.py",
            "api": {
                "body": {
                    "objective": (
                        "Turn R10 instability evidence into category-level remediation rules for "
                        f"{', '.join(instability) or 'the unstable subset'}."
                    ),
                    "risk_class": "medium",
                    "acceptance_criteria": [
                        "The R10 unstable categories remain excluded from canonical promotion until stability improves.",
                        "The R12 report records instability drivers and affected case IDs.",
                        "A rerun can compare instability_rate before and after remediation.",
                    ],
                    "metadata": {"recommended_loop": "openmythos-r12-active-evolution"},
                }
            },
        },
        {
            "key": "om-r12-02-expand-oracle-anchor-coverage",
            "title": "Expand oracle and gold-anchor coverage",
            "risk": "medium",
            "target": "openmythos-benchmark/scripts/oracle_score.py",
            "depends_on": ["om-r12-01-stabilize-low-reliability-categories"],
            "api": {
                "body": {
                    "objective": (
                        "Add reliable oracle or gold-anchor coverage for top evidence gaps: "
                        f"{', '.join(oracle_gap) or 'none'}."
                    ),
                    "risk_class": "medium",
                    "acceptance_criteria": [
                        "Each selected category has explicit anchor evidence or a documented reason deterministic checks are unsafe.",
                        "Temporal checks are deterministic where date/timezone facts are structurally available.",
                        "Non-deterministic categories use curated gold anchors rather than fragile regex scoring.",
                    ],
                    "metadata": {"recommended_loop": "openmythos-r12-active-evolution"},
                }
            },
        },
        {
            "key": "om-r12-03-rewrite-dead-or-nondiscriminating-cases",
            "title": "Rewrite dead or nondiscriminating cases",
            "risk": "medium",
            "target": "openmythos-benchmark/cases/corpus.jsonl",
            "depends_on": ["om-r12-02-expand-oracle-anchor-coverage"],
            "api": {
                "body": {
                    "objective": (
                        "Replace or revise low-signal cases in "
                        f"{', '.join(weak) or 'the weakest categories'}; initial queue: "
                        f"{', '.join(dead_cases) or 'none'}."
                    ),
                    "risk_class": "medium",
                    "acceptance_criteria": [
                        "Rewritten cases increase model spread without becoming judge-unstable.",
                        "All case mutations pass corpus validation and preserve schema requirements.",
                        "Promotion remains draft until R10 reliability and R11 calibrated weighting agree.",
                    ],
                    "metadata": {"recommended_loop": "openmythos-r12-active-evolution"},
                }
            },
        },
        {
            "key": "om-r12-04-close-calibration-bias-loop",
            "title": "Close calibration bias loop",
            "risk": "medium",
            "target": "openmythos-benchmark/scripts/calibrated_leaderboard.py",
            "depends_on": ["om-r12-02-expand-oracle-anchor-coverage"],
            "api": {
                "body": {
                    "objective": (
                        "Use R11 anchor agreement and strictness bias to quarantine weak judge/category pairs "
                        "before leaderboard or promotion decisions."
                    ),
                    "risk_class": "medium",
                    "acceptance_criteria": [
                        "Judge/category pairs below the calibration floor are marked as discounted or quarantined.",
                        "The calibrated leaderboard reports calibration drivers that affected weights.",
                        "At least one before/after report proves the weighting changed only evidence-backed cases.",
                    ],
                    "metadata": {"recommended_loop": "openmythos-r12-active-evolution"},
                }
            },
        },
        {
            "key": "om-r12-05-promotion-firewall",
            "title": "Add active-evolution promotion firewall",
            "risk": "low",
            "target": "openmythos-benchmark/scripts/promotion_gate.py",
            "depends_on": [
                "om-r12-01-stabilize-low-reliability-categories",
                "om-r12-03-rewrite-dead-or-nondiscriminating-cases",
                "om-r12-04-close-calibration-bias-loop",
            ],
            "api": {
                "body": {
                    "objective": (
                        "Require discrimination, judge stability, oracle compatibility, and calibrated "
                        "case weight before a draft case can become canonical."
                    ),
                    "risk_class": "low",
                    "acceptance_criteria": [
                        "A case with low reliability cannot be promoted even if it discriminates.",
                        "A case with oracle disagreement cannot be promoted without explicit review evidence.",
                        "The gate emits machine-readable reasons for every accepted and rejected case.",
                    ],
                    "metadata": {"recommended_loop": "openmythos-r12-active-evolution"},
                }
            },
        },
    ]


def build_report(
    weakness: dict,
    reliability: dict,
    promotion: dict,
    calibrated: dict,
    anchors: list[dict],
    min_anchor_count: int,
) -> dict:
    priorities = category_priorities(weakness, reliability, promotion, calibrated, anchors, min_anchor_count)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "common_cases": calibrated.get("leaderboard", {}).get("benchmark", {}).get("common_cases"),
            "weighted_discrimination": calibrated.get("leaderboard", {}).get("benchmark", {}).get("weighted_discrimination"),
            "gold_anchors": calibrated.get("calibration", {}).get("anchors"),
            "r10_unstable_cases": len(reliability.get("unstable_cases", [])),
            "r10_promoted_cases": len(promotion.get("promoted", [])),
            "r10_rejected_cases": len(promotion.get("rejected", [])),
            "min_anchor_count": min_anchor_count,
        },
        "category_priorities": priorities,
        "dead_or_low_spread_cases": top_dead_cases(
            weakness,
            [row["category"] for row in priorities if "weak-category" in row["drivers"]],
        ),
    }
    report["djimitflo_goals"] = build_goals(report)
    return report


def build_goal_batch(report: dict, change_id: str) -> dict:
    return {
        "change": change_id,
        "source": "OpenMythos R12 active evolution queue",
        "generated_at": report["generated_at"],
        "writes_expected_in_preview": 0,
        "human_interactions_at_end": [
            "Approve Djimitflo goal-batch apply after preview remains valid and blocked=0.",
            "Approve canonical case promotion only after R10, R11, and R12 evidence stays green.",
        ],
        "ordered_goals": report["djimitflo_goals"],
    }


def render_markdown(report: dict, batch: dict) -> str:
    lines = [
        "# OpenMythos Apex R12 Active Evolution Queue",
        "",
        "## Evidence Summary",
        "",
        f"- common calibrated cases: `{report['inputs']['common_cases']}`",
        f"- weighted discrimination: `{report['inputs']['weighted_discrimination']}`",
        f"- gold anchors: `{report['inputs']['gold_anchors']}`",
        f"- R10 unstable cases: `{report['inputs']['r10_unstable_cases']}`",
        f"- R10 promoted cases: `{report['inputs']['r10_promoted_cases']}`",
        f"- R10 rejected cases: `{report['inputs']['r10_rejected_cases']}`",
        "",
        "## Category Priority",
        "",
        "| rank | category | priority | drivers | weakness | instability | anchors | oracle gap | calibration gap |",
        "|---:|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(report["category_priorities"], 1):
        drivers = ", ".join(row["drivers"]) or "-"
        lines.append(
            f"| {rank} | {row['category']} | {row['priority']:.3f} | {drivers} | "
            f"{row['weakness']:.3f} | {row['instability_rate']:.3f} | "
            f"{row['anchor_count']} | {row['oracle_gap']:.3f} | {row['calibration_gap']:.3f} |"
        )

    lines.extend(
        [
            "",
            "## Djimitflo Goal Batch",
            "",
            f"- change: `{batch['change']}`",
            f"- ordered goals: `{len(batch['ordered_goals'])}`",
            "- preview expectation: `writes=0`",
            "",
            "| order | goal | risk | target |",
            "|---:|---|---|---|",
        ]
    )
    for idx, goal in enumerate(batch["ordered_goals"], 1):
        lines.append(f"| {idx} | {goal['key']} | {goal['risk']} | {goal['target']} |")

    lines.extend(
        [
            "",
            "## Human Interactions At End",
            "",
        ]
    )
    for item in batch["human_interactions_at_end"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def demo() -> int:
    weakness = {
        "categories": [
            {"category": "tool-scope", "weakness": 1.5, "dead_rate": 0.4, "avg_spread": 1.2, "cases": 4},
            {"category": "temporal-reasoning", "weakness": 1.2, "dead_rate": 0.2, "avg_spread": 2.0, "cases": 4},
        ],
        "cases": [{"case_id": "tool-scope-001", "spread": 0, "dead": True, "all_pass": False, "all_fail": True}],
    }
    reliability = {"categories": [{"category": "tool-scope", "instability_rate": 1.0}], "unstable_cases": [{"case_id": "x"}]}
    promotion = {"promoted": [], "rejected": [{"case_id": "x"}], "categories": {"tool-scope": {"dead_rate": 0.5}}}
    calibrated = {
        "calibration": {
            "anchors": 3,
            "categories": [{"category": "tool-scope", "agreement_rate": 0.25, "weight": 0.25}],
        },
        "leaderboard": {"benchmark": {"common_cases": 2, "weighted_discrimination": 0.5}},
    }
    anchors = [{"category": "tool-scope", "judge_agrees": False, "oracle_type": "tool_scope_boundary"}]
    report = build_report(weakness, reliability, promotion, calibrated, anchors, min_anchor_count=4)
    batch = build_goal_batch(report, "demo")
    assert report["category_priorities"][0]["category"] == "tool-scope", report
    assert len(batch["ordered_goals"]) == 5, batch
    assert "om-r12-05-promotion-firewall" in render_markdown(report, batch)
    print("demo OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weakness", type=Path, default=REPORT_DIR / "apex-r9-promotion-weakness-map.json")
    parser.add_argument("--reliability", type=Path, default=REPORT_DIR / "apex-r10-judge-reliability.json")
    parser.add_argument("--promotion", type=Path, default=REPORT_DIR / "apex-r10-promotion-gate.json")
    parser.add_argument("--calibrated", type=Path, default=REPORT_DIR / "apex-r11-calibrated-leaderboard.json")
    parser.add_argument("--anchors", type=Path, default=REPORT_DIR / "apex-r11-gold-anchors.jsonl")
    parser.add_argument("--min-anchor-count", type=int, default=6)
    parser.add_argument("--change-id", default="openmythos-apex-r12-djimitflo-active-evolution")
    parser.add_argument("--json-output", type=Path, default=REPORT_DIR / "apex-r12-active-evolution-queue.json")
    parser.add_argument("--output", type=Path, default=REPORT_DIR / "APEX_R12_ACTIVE_EVOLUTION_QUEUE.md")
    parser.add_argument("--goal-batch-output", type=Path, default=REPORT_DIR / "apex-r12-djimitflo-goals.batch.json")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo:
        return demo()

    report = build_report(
        load_json(args.weakness),
        load_json(args.reliability),
        load_json(args.promotion),
        load_json(args.calibrated),
        load_jsonl(args.anchors),
        args.min_anchor_count,
    )
    batch = build_goal_batch(report, args.change_id)
    write_json(args.json_output, report)
    write_json(args.goal_batch_output, batch)
    write_text(args.output, render_markdown(report, batch))
    print(f"Wrote {args.output}")
    print(f"Wrote {args.json_output}")
    print(f"Wrote {args.goal_batch_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
