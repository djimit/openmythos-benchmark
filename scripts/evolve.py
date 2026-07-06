#!/usr/bin/env python3
"""Create the next OpenMythos evolution step from judged traces."""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_corpus(path: Path) -> dict[str, dict]:
    return {row["id"]: row for row in load_jsonl(path)}


def load_trace(path: Path) -> tuple[str, dict[str, dict]]:
    rows = load_jsonl(path)
    name = rows[0].get("model") if rows else path.stem.replace("judged_", "")
    return name, {row["case_id"]: row for row in rows if "judge_score" in row}


def mean(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def case_action(avg_score: float, spread: int) -> str:
    if spread == 0 and avg_score >= 4:
        return "rewrite_easy_dead"
    if spread == 0 and avg_score <= 2:
        return "rewrite_too_hard_dead"
    if spread == 0:
        return "rewrite_dead"
    if spread >= 2:
        return "keep_discriminating"
    if avg_score < 3:
        return "inspect_weak"
    return "keep"


def category_action(avg_spread: float, dead_rate: float) -> str:
    if avg_spread >= 2 and dead_rate <= 0.25:
        return "expand"
    if dead_rate >= 0.75:
        return "replace"
    if dead_rate >= 0.5 or avg_spread < 0.75:
        return "rewrite"
    return "keep"


def analyze(corpus: dict[str, dict], traces: dict[str, dict[str, dict]]) -> dict:
    common = sorted(set.intersection(*(set(rows) for rows in traces.values())))
    cases = []
    categories = defaultdict(list)

    for case_id in common:
        scores = {model: rows[case_id]["judge_score"] for model, rows in traces.items()}
        values = list(scores.values())
        row = corpus.get(case_id, {})
        category = row.get("category") or next(iter(traces.values()))[case_id].get("category", "unknown")
        spread = max(values) - min(values)
        avg_score = mean(values)
        item = {
            "case_id": case_id,
            "category": category,
            "subcategory": row.get("subcategory", ""),
            "difficulty": row.get("difficulty"),
            "failure_mode": row.get("failure_mode", ""),
            "avg_score": round(avg_score, 3),
            "spread": spread,
            "scores": scores,
            "action": case_action(avg_score, spread),
        }
        cases.append(item)
        categories[category].append(item)

    category_rows = []
    for category, items in sorted(categories.items()):
        avg_spread = mean(item["spread"] for item in items)
        dead_rate = sum(1 for item in items if item["spread"] == 0) / len(items)
        avg_score = mean(item["avg_score"] for item in items)
        action = category_action(avg_spread, dead_rate)
        category_rows.append(
            {
                "category": category,
                "cases": len(items),
                "avg_score": round(avg_score, 3),
                "avg_spread": round(avg_spread, 3),
                "dead_rate": round(dead_rate, 3),
                "action": action,
            }
        )

    tasks = build_tasks(category_rows, cases)
    return {
        "models": list(traces),
        "common_cases": len(common),
        "category_rows": category_rows,
        "case_rows": sorted(cases, key=lambda x: (x["action"] == "keep", -x["spread"], x["case_id"])),
        "tasks": tasks,
    }


def build_tasks(categories: list[dict], cases: list[dict]) -> list[dict]:
    tasks = []
    weak_categories = [c for c in categories if c["action"] in {"replace", "rewrite"}]
    strong_categories = [c for c in categories if c["action"] == "expand"]

    for cat in sorted(weak_categories, key=lambda c: (-c["dead_rate"], c["avg_spread"]))[:4]:
        dead = [c for c in cases if c["category"] == cat["category"] and c["spread"] == 0]
        tasks.append(
            {
                "type": cat["action"],
                "category": cat["category"],
                "reason": f"dead_rate={cat['dead_rate']}, avg_spread={cat['avg_spread']}",
                "case_ids": [c["case_id"] for c in dead],
                "instruction": "Rewrite these cases with a harder multi-constraint scenario and measurable expected_behavior.",
            }
        )

    for cat in sorted(strong_categories, key=lambda c: -c["avg_spread"])[:3]:
        tasks.append(
            {
                "type": "expand",
                "category": cat["category"],
                "reason": f"avg_spread={cat['avg_spread']}, dead_rate={cat['dead_rate']}",
                "case_ids": [],
                "instruction": "Add adjacent cases near this category; it currently separates stronger and weaker models.",
            }
        )

    return tasks


def goal_batch_from_tasks(tasks: list[dict], change: str = "openmythos-evolution-best-in-class") -> dict:
    goals = []
    for index, task in enumerate(tasks, 1):
        category = task["category"]
        action = task["type"]
        ids = ", ".join(task["case_ids"]) if task["case_ids"] else "new adjacent cases"
        goals.append(
            {
                "id": f"om-evo-{index:02d}",
                "objective": (
                    f"{action.upper()} OpenMythos `{category}` cases based on current judged-trace "
                    f"evolution evidence. Scope: {ids}. {task['instruction']}"
                ),
                "risk_class": "medium" if action in {"replace", "rewrite"} else "low",
                "target": f"openmythos-benchmark/cases/{category}",
                "acceptance_criteria": [
                    "Draft corpus changes validate with scripts/validate_jsonl.py or scripts/validate.py",
                    "Same model set is re-run through scripts/run_benchmark.py",
                    "Judged traces are produced with one consistent judge model",
                    "scripts/evolve.py reports lower dead-case rate for this category",
                    "Category discrimination does not decrease versus the current EVOLUTION_STEP.md baseline",
                ],
            }
        )
    return {"change": change, "ordered_goals": goals}


def render(report: dict) -> str:
    lines = [
        "# OpenMythos Evolution Step",
        "",
        f"- models: {', '.join(f'`{m}`' for m in report['models'])}",
        f"- common judged cases: {report['common_cases']}",
        "",
        "## Category Decision",
        "",
        "| category | cases | avg score | spread | dead rate | action |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in report["category_rows"]:
        lines.append(
            f"| {row['category']} | {row['cases']} | {row['avg_score']:.2f} | "
            f"{row['avg_spread']:.2f} | {row['dead_rate']:.2f} | {row['action']} |"
        )

    lines.extend(["", "## Next Tasks", ""])
    for i, task in enumerate(report["tasks"], 1):
        ids = ", ".join(task["case_ids"]) if task["case_ids"] else "new adjacent cases"
        lines.append(
            f"{i}. `{task['type']}` `{task['category']}` - {task['reason']} - {ids}. "
            f"{task['instruction']}"
        )

    lines.extend(["", "## Case Triage", ""])
    lines.append("| case | category | avg | spread | action |")
    lines.append("|---|---|---:|---:|---|")
    for row in report["case_rows"][:40]:
        lines.append(
            f"| {row['case_id']} | {row['category']} | {row['avg_score']:.2f} | "
            f"{row['spread']} | {row['action']} |"
        )

    lines.extend(
        [
            "",
            "## Loop",
            "",
            "1. Rewrite or replace the listed dead cases in a draft corpus.",
            "2. Run the same model set through `scripts/run_benchmark.py`.",
            "3. Judge all traces with the same judge.",
            "4. Re-run `scripts/evolve.py` and keep only changes that reduce dead rate without lowering discrimination.",
            "",
        ]
    )
    return "\n".join(lines)


def demo() -> int:
    corpus = {
        "a": {"id": "a", "category": "strong"},
        "b": {"id": "b", "category": "dead"},
    }
    traces = {
        "big": {"a": {"judge_score": 5}, "b": {"judge_score": 4}},
        "small": {"a": {"judge_score": 2}, "b": {"judge_score": 4}},
    }
    report = analyze(corpus, traces)
    assert report["common_cases"] == 2
    assert any(c["category"] == "strong" and c["action"] == "expand" for c in report["category_rows"])
    assert any(c["category"] == "dead" and c["action"] in {"replace", "rewrite"} for c in report["category_rows"])
    assert "OpenMythos Evolution Step" in render(report)
    print("demo OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", nargs="*", type=Path)
    parser.add_argument("--corpus", type=Path, default=REPO_ROOT / "cases" / "corpus.jsonl")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--tasks", type=Path)
    parser.add_argument("--goal-batch", type=Path)
    parser.add_argument("--change", default="openmythos-evolution-best-in-class")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo:
        return demo()
    if len(args.traces) < 2:
        parser.error("need at least 2 judged traces or --demo")

    corpus = load_corpus(args.corpus)
    traces = dict(load_trace(path) for path in args.traces)
    report = analyze(corpus, traces)
    markdown = render(report)

    if args.tasks:
        args.tasks.parent.mkdir(parents=True, exist_ok=True)
        args.tasks.write_text(json.dumps(report["tasks"], indent=2))
    if args.goal_batch:
        args.goal_batch.parent.mkdir(parents=True, exist_ok=True)
        args.goal_batch.write_text(json.dumps(goal_batch_from_tasks(report["tasks"], args.change), indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown)
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
