#!/usr/bin/env python3
"""Create a weakness map from judged OpenMythos traces."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_trace(path: Path) -> tuple[str, dict[str, dict]]:
    rows = load_jsonl(path)
    model = rows[0].get("model") if rows else path.stem.replace("judged_", "")
    return model, {row["case_id"]: row for row in rows if "judge_score" in row}


def mean(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def rate(rows: list[dict], key: str) -> float:
    return sum(1 for row in rows if row[key]) / len(rows) if rows else 0.0


def analyze(corpus: dict[str, dict], traces: dict[str, dict[str, dict]]) -> dict:
    common = sorted(set.intersection(*(set(rows) for rows in traces.values())))
    by_category = defaultdict(list)
    cases = []

    for case_id in common:
        scores = {model: rows[case_id]["judge_score"] for model, rows in traces.items()}
        values = list(scores.values())
        case = corpus.get(case_id, {})
        category = case.get("category") or next(iter(traces.values()))[case_id].get("category", "unknown")
        spread = max(values) - min(values)
        avg_score = mean(values)
        row = {
            "case_id": case_id,
            "category": category,
            "avg_score": round(avg_score, 3),
            "spread": spread,
            "dead": spread == 0,
            "all_pass": min(values) >= 4,
            "all_fail": max(values) <= 2,
            "scores": scores,
        }
        cases.append(row)
        by_category[category].append(row)

    categories = []
    for category, rows in sorted(by_category.items()):
        avg_score = mean(r["avg_score"] for r in rows)
        avg_spread = mean(r["spread"] for r in rows)
        dead_rate = rate(rows, "dead")
        all_pass_rate = rate(rows, "all_pass")
        all_fail_rate = rate(rows, "all_fail")
        # ponytail: transparent heuristic; replace with IRT only after repeated full-run evidence.
        weakness = dead_rate * 2 + all_pass_rate + all_fail_rate + max(0, 1.5 - avg_spread)
        categories.append(
            {
                "category": category,
                "cases": len(rows),
                "avg_score": round(avg_score, 3),
                "avg_spread": round(avg_spread, 3),
                "dead_rate": round(dead_rate, 3),
                "all_pass_rate": round(all_pass_rate, 3),
                "all_fail_rate": round(all_fail_rate, 3),
                "weakness": round(weakness, 3),
            }
        )

    return {
        "models": list(traces),
        "common_cases": len(common),
        "categories": sorted(categories, key=lambda r: (-r["weakness"], r["category"])),
        "cases": sorted(cases, key=lambda r: (not r["dead"], r["spread"], r["case_id"])),
    }


def render(report: dict, top: int) -> str:
    lines = [
        "# OpenMythos Weakness Map",
        "",
        f"- models: {', '.join(f'`{m}`' for m in report['models'])}",
        f"- common judged cases: `{report['common_cases']}`",
        "",
        "## Weakest Categories",
        "",
        "| category | cases | avg score | spread | dead | all-pass | all-fail | weakness |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["categories"]:
        lines.append(
            f"| {row['category']} | {row['cases']} | {row['avg_score']:.2f} | "
            f"{row['avg_spread']:.2f} | {row['dead_rate']:.2f} | "
            f"{row['all_pass_rate']:.2f} | {row['all_fail_rate']:.2f} | {row['weakness']:.2f} |"
        )

    lines.extend(["", f"## Top {top} Dead Or Low-Spread Cases", ""])
    lines.append("| case | category | avg | spread | flags |")
    lines.append("|---|---|---:|---:|---|")
    for row in report["cases"][:top]:
        flags = [name for name in ("dead", "all_pass", "all_fail") if row[name]]
        lines.append(
            f"| {row['case_id']} | {row['category']} | {row['avg_score']:.2f} | "
            f"{row['spread']} | {', '.join(flags) or '-'} |"
        )
    lines.append("")
    return "\n".join(lines)


def demo() -> int:
    corpus = {"a": {"id": "a", "category": "tool-scope"}, "b": {"id": "b", "category": "hierarchy"}}
    report = analyze(
        corpus,
        {
            "strong": {"a": {"judge_score": 5}, "b": {"judge_score": 5}},
            "weak": {"a": {"judge_score": 5}, "b": {"judge_score": 2}},
        },
    )
    assert report["common_cases"] == 2, report
    assert report["categories"][0]["category"] == "tool-scope", report
    assert "Weakness Map" in render(report, 2)
    print("demo OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", nargs="*", type=Path)
    parser.add_argument("--corpus", type=Path, default=REPO_ROOT / "cases" / "corpus.jsonl")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo:
        return demo()
    if len(args.traces) < 2:
        parser.error("need at least 2 judged traces or --demo")

    corpus = {row["id"]: row for row in load_jsonl(args.corpus)}
    report = analyze(corpus, dict(load_trace(path) for path in args.traces))
    markdown = render(report, args.top)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown)
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
