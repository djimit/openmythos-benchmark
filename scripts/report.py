#!/usr/bin/env python3
"""Create a Markdown report from an OpenMythos/OpenGPT5 trace."""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def avg(values) -> float:
    values = [v for v in values if isinstance(v, (int, float))]
    return sum(values) / len(values) if values else 0.0


def summarize(rows: list[dict]) -> dict:
    by_category = defaultdict(list)
    for row in rows:
        by_category[row.get("category", "unknown")].append(row)

    judged = [r for r in rows if "judge_score" in r]
    errors = [r for r in rows if str(r.get("response", "")).startswith("ERROR")]

    return {
        "cases": len(rows),
        "model": rows[0].get("model", "unknown") if rows else "unknown",
        "backend": rows[0].get("backend", "unknown") if rows else "unknown",
        "errors": len(errors),
        "avg_latency_ms": avg(r.get("latency_ms", 0) for r in rows),
        "avg_tokens": avg(r.get("tokens", 0) for r in rows),
        "judged_cases": len(judged),
        "avg_judge_score": avg(r.get("judge_score", 0) for r in judged),
        "pass_rate": (
            sum(1 for r in judged if r.get("judge_score", 0) >= 4) / len(judged) * 100
            if judged
            else 0.0
        ),
        "categories": {
            cat: {
                "cases": len(items),
                "errors": sum(1 for r in items if str(r.get("response", "")).startswith("ERROR")),
                "avg_latency_ms": avg(r.get("latency_ms", 0) for r in items),
                "avg_tokens": avg(r.get("tokens", 0) for r in items),
                "avg_judge_score": avg(r.get("judge_score", 0) for r in items if "judge_score" in r),
                "pass_rate": (
                    sum(1 for r in items if r.get("judge_score", 0) >= 4)
                    / sum(1 for r in items if "judge_score" in r)
                    * 100
                    if any("judge_score" in r for r in items)
                    else 0.0
                ),
            }
            for cat, items in sorted(by_category.items())
        },
    }


def render_markdown(summary: dict, trace: Path, title: str) -> str:
    judged = summary["judged_cases"] > 0
    lines = [
        f"# {title}",
        "",
        f"- trace: `{trace}`",
        f"- model: `{summary['model']}`",
        f"- backend: `{summary['backend']}`",
        f"- cases: {summary['cases']}",
        f"- errors: {summary['errors']}",
        f"- avg latency: {summary['avg_latency_ms']:.1f} ms",
        f"- avg tokens: {summary['avg_tokens']:.1f}",
    ]
    if judged:
        lines.extend(
            [
                f"- judged cases: {summary['judged_cases']}",
                f"- avg judge score: {summary['avg_judge_score']:.2f}/5",
                f"- pass rate: {summary['pass_rate']:.1f}%",
            ]
        )

    lines.extend(["", "## Categories", ""])
    if judged:
        lines.append("| category | cases | avg score | pass rate | avg ms | errors |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for cat, row in summary["categories"].items():
            lines.append(
                f"| {cat} | {row['cases']} | {row['avg_judge_score']:.2f} | "
                f"{row['pass_rate']:.1f}% | {row['avg_latency_ms']:.1f} | {row['errors']} |"
            )
    else:
        lines.append("| category | cases | avg ms | avg tokens | errors |")
        lines.append("|---|---:|---:|---:|---:|")
        for cat, row in summary["categories"].items():
            lines.append(
                f"| {cat} | {row['cases']} | {row['avg_latency_ms']:.1f} | "
                f"{row['avg_tokens']:.1f} | {row['errors']} |"
            )
    lines.append("")
    return "\n".join(lines)


def demo() -> int:
    rows = [
        {"case_id": "a", "category": "x", "model": "m", "backend": "b", "tokens": 10, "latency_ms": 100, "response": "ok", "judge_score": 5},
        {"case_id": "b", "category": "x", "model": "m", "backend": "b", "tokens": 20, "latency_ms": 200, "response": "ok", "judge_score": 3},
    ]
    s = summarize(rows)
    assert s["cases"] == 2
    assert s["avg_judge_score"] == 4
    assert s["pass_rate"] == 50
    assert "| x | 2 | 4.00 | 50.0%" in render_markdown(s, Path("demo.jsonl"), "Demo")
    print("demo OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", type=Path, required=False)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--title", default="Benchmark Report")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo:
        return demo()
    if not args.trace:
        parser.error("--trace is required unless --demo is used")

    summary = summarize(load_jsonl(args.trace))
    report = render_markdown(summary, args.trace, args.title)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report)
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
