#!/usr/bin/env python3
"""Create a simple leaderboard and optional regression delta from judged traces."""

import argparse
import json
from collections import defaultdict
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def mean(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def pass_rate(rows: list[dict]) -> float:
    return sum(1 for row in rows if row["judge_score"] >= 4) / len(rows) if rows else 0.0


def model_name(path: Path, rows: list[dict]) -> str:
    return rows[0].get("model") if rows else path.stem.replace("judged_", "")


def summarize_trace(path: Path) -> dict:
    rows = load_jsonl(path)
    judged = [r for r in rows if "judge_score" in r]
    categories = defaultdict(list)
    for row in judged:
        categories[row.get("category", "unknown")].append(row)
    return {
        "model": model_name(path, rows),
        "trace": str(path),
        "cases": len(rows),
        "judged_cases": len(judged),
        "avg_score": round(mean(r["judge_score"] for r in judged), 3),
        "pass_rate": round(pass_rate(judged), 3),
        "errors": sum(1 for r in rows if str(r.get("response", "")).startswith("ERROR")),
        "avg_latency_ms": round(mean(r.get("latency_ms", 0) for r in rows), 1),
        "avg_tokens": round(mean(r.get("tokens", 0) for r in rows), 1),
        "categories": {
            cat: {
                "cases": len(items),
                "avg_score": round(mean(r["judge_score"] for r in items), 3),
                "pass_rate": round(pass_rate(items), 3),
            }
            for cat, items in sorted(categories.items())
        },
    }


def discrimination(paths: list[Path]) -> dict:
    traces = {}
    for path in paths:
        rows = load_jsonl(path)
        traces[model_name(path, rows)] = {r["case_id"]: r for r in rows if "judge_score" in r}
    common = sorted(set.intersection(*(set(rows) for rows in traces.values()))) if traces else []
    dead = 0
    spreads = []
    for case_id in common:
        scores = [rows[case_id]["judge_score"] for rows in traces.values()]
        spreads.append(max(scores) - min(scores))
        dead += max(scores) == min(scores)
    model_avgs = {
        model: mean(rows[case_id]["judge_score"] for case_id in common)
        for model, rows in traces.items()
    }
    return {
        "common_cases": len(common),
        "discrimination": round(max(model_avgs.values()) - min(model_avgs.values()), 3) if model_avgs else 0,
        "dead_case_rate": round(dead / len(common), 3) if common else 0,
        "avg_case_spread": round(mean(spreads), 3),
    }


def build(paths: list[Path], baseline: Path | None = None) -> dict:
    current = {
        "models": sorted((summarize_trace(path) for path in paths), key=lambda r: -r["avg_score"]),
        "benchmark": discrimination(paths),
    }
    if baseline and baseline.exists():
        old = json.loads(baseline.read_text())
        old_models = {row["model"]: row for row in old.get("models", [])}
        old_set = set(old_models)
        new_set = {row["model"] for row in current["models"]}
        current["baseline_model_set_changed"] = old_set != new_set
        current["regression"] = [
            {
                "model": row["model"],
                "avg_score_delta": round(row["avg_score"] - old_models[row["model"]]["avg_score"], 3),
                "pass_rate_delta": round(row["pass_rate"] - old_models[row["model"]]["pass_rate"], 3),
            }
            for row in current["models"]
            if row["model"] in old_models
        ]
        old_bench = old.get("benchmark", {})
        if old_set == new_set:
            current["benchmark_delta"] = {
                "discrimination_delta": round(current["benchmark"]["discrimination"] - old_bench.get("discrimination", 0), 3),
                "dead_case_rate_delta": round(current["benchmark"]["dead_case_rate"] - old_bench.get("dead_case_rate", 0), 3),
            }
    return current


def render(report: dict) -> str:
    lines = [
        "# OpenMythos Leaderboard",
        "",
        f"- common cases: `{report['benchmark']['common_cases']}`",
        f"- discrimination: `{report['benchmark']['discrimination']}`",
        f"- dead-case rate: `{report['benchmark']['dead_case_rate']}`",
        f"- avg case spread: `{report['benchmark']['avg_case_spread']}`",
        "",
        "| rank | model | avg score | pass rate | cases | errors | avg ms | avg tokens |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(report["models"], 1):
        lines.append(
            f"| {rank} | {row['model']} | {row['avg_score']:.3f} | {row['pass_rate']:.3f} | "
            f"{row['judged_cases']} | {row['errors']} | {row['avg_latency_ms']:.1f} | {row['avg_tokens']:.1f} |"
        )
    if report.get("regression"):
        lines.extend(["", "## Regression Delta", "", "| model | avg score delta | pass rate delta |", "|---|---:|---:|"])
        for row in report["regression"]:
            lines.append(f"| {row['model']} | {row['avg_score_delta']:+.3f} | {row['pass_rate_delta']:+.3f} |")
        lines.append("")
        if report.get("baseline_model_set_changed"):
            lines.append("- benchmark delta skipped: baseline and current model sets differ")
        else:
            delta = report.get("benchmark_delta", {})
            lines.extend(
                [
                    f"- discrimination delta: `{delta.get('discrimination_delta', 0):+.3f}`",
                    f"- dead-case-rate delta: `{delta.get('dead_case_rate_delta', 0):+.3f}`",
                ]
            )
    lines.append("")
    return "\n".join(lines)


def demo() -> int:
    report = {
        "models": [
            {"model": "m1", "avg_score": 4, "pass_rate": 1, "judged_cases": 1, "errors": 0, "avg_latency_ms": 10, "avg_tokens": 5}
        ],
        "benchmark": {"common_cases": 1, "discrimination": 0, "dead_case_rate": 1, "avg_case_spread": 0},
    }
    assert "OpenMythos Leaderboard" in render(report)
    print("demo OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", nargs="*", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo:
        return demo()
    if len(args.traces) < 2:
        parser.error("need at least 2 judged traces or --demo")

    report = build(args.traces, args.baseline)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2))
    markdown = render(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown)
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
