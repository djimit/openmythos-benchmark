#!/usr/bin/env python3
"""Reject draft cases that add no stable discriminating benchmark value."""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def load(path: Path) -> dict[str, dict]:
    rows = {}
    with path.open() as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                if "judge_score" not in row:
                    raise SystemExit(f"{path} is missing judge_score")
                rows[row["case_id"]] = row
    return rows


def load_reliability(path: Path | None) -> dict[str, dict]:
    if not path:
        return {}
    text = path.read_text().strip()
    if not text:
        return {}
    if text[0] == "{":
        try:
            payload = json.loads(text)
            rows = payload.get("cases", [])
        except json.JSONDecodeError:
            rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    return {row["case_id"]: row for row in rows}


def load_oracle(path: Path | None) -> dict[str, list[dict]]:
    if not path:
        return {}
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    out = defaultdict(list)
    for row in rows:
        if row.get("oracle_applicable"):
            out[row["case_id"]].append(row)
    return dict(out)


def analyze(
    traces: dict[str, dict[str, dict]],
    pass_score: int = 4,
    min_spread: int = 2,
    reliability: dict[str, dict] | None = None,
    oracle: dict[str, list[dict]] | None = None,
) -> dict:
    reliability = reliability or {}
    oracle = oracle or {}
    common = sorted(set.intersection(*(set(trace) for trace in traces.values())))
    decisions = []
    by_category = defaultdict(lambda: {"n": 0, "dead": 0})

    for case_id in common:
        rows = [trace[case_id] for trace in traces.values()]
        scores = [row["judge_score"] for row in rows]
        category = rows[0].get("category", "unknown")
        spread = max(scores) - min(scores)
        all_pass = min(scores) >= pass_score
        all_fail = max(scores) < pass_score
        rel = reliability.get(case_id, {})
        oracle_rows = oracle.get(case_id, [])
        oracle_disagreement = any(row.get("oracle_judge_disagreement") for row in oracle_rows)

        by_category[category]["n"] += 1
        if spread == 0:
            by_category[category]["dead"] += 1

        reasons = []
        if spread < min_spread:
            reasons.append(f"spread={spread}<{min_spread}")
        if all_pass:
            reasons.append("all-pass")
        if all_fail:
            reasons.append("all-fail")
        if rel.get("low_reliability"):
            reasons.append("low-reliability")
        if oracle_disagreement:
            reasons.append("oracle-disagreement")

        decisions.append(
            {
                "case_id": case_id,
                "category": category,
                "scores": {name: traces[name][case_id]["judge_score"] for name in traces},
                "spread": spread,
                "avg_score": round(sum(scores) / len(scores), 3),
                "all_pass": all_pass,
                "all_fail": all_fail,
                "low_reliability": bool(rel.get("low_reliability")),
                "oracle_disagreement": oracle_disagreement,
                "decision": "reject" if reasons else "promote",
                "reason": ", ".join(reasons) if reasons else "spread and stability gates passed",
            }
        )

    categories = {
        category: {
            "n": values["n"],
            "dead_rate": values["dead"] / values["n"] if values["n"] else 0.0,
        }
        for category, values in sorted(by_category.items())
    }
    return {
        "common_cases": len(common),
        "promoted": [row for row in decisions if row["decision"] == "promote"],
        "rejected": [row for row in decisions if row["decision"] == "reject"],
        "decisions": decisions,
        "categories": categories,
        "thresholds": {"pass_score": pass_score, "min_spread": min_spread},
    }


def render(report: dict) -> str:
    lines = [
        "# OpenMythos Promotion Gate",
        "",
        f"- common cases: `{report['common_cases']}`",
        f"- promoted: `{len(report['promoted'])}`",
        f"- rejected: `{len(report['rejected'])}`",
        f"- min spread: `{report['thresholds']['min_spread']}`",
        "",
        "## Category Dead Rates",
        "",
        "| category | cases | dead rate |",
        "|---|---:|---:|",
    ]
    for category, stats in report["categories"].items():
        lines.append(f"| {category} | {stats['n']} | {stats['dead_rate']:.3f} |")
    lines.extend(["", "## Decisions", "", "| case | category | decision | spread | reason |", "|---|---|---|---:|---|"])
    for row in report["decisions"]:
        lines.append(f"| {row['case_id']} | {row['category']} | {row['decision']} | {row['spread']} | {row['reason']} |")
    lines.append("")
    return "\n".join(lines)


def write_json(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")


def write_promoted(path: Path, report: dict, corpus: Path) -> None:
    wanted = {row["case_id"] for row in report["promoted"]}
    rows = [json.loads(line) for line in corpus.read_text().splitlines() if line.strip()]
    selected = [row for row in rows if row.get("id") in wanted or row.get("case_id") in wanted]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in selected))


def demo() -> int:
    report = analyze(
        {
            "weak": {
                "dead": {"case_id": "dead", "category": "overthinking", "judge_score": 5},
                "good": {"case_id": "good", "category": "overthinking", "judge_score": 2},
                "unstable": {"case_id": "unstable", "category": "canary", "judge_score": 1},
            },
            "strong": {
                "dead": {"case_id": "dead", "category": "overthinking", "judge_score": 5},
                "good": {"case_id": "good", "category": "overthinking", "judge_score": 5},
                "unstable": {"case_id": "unstable", "category": "canary", "judge_score": 5},
            },
        },
        reliability={"unstable": {"low_reliability": True}},
    )
    promoted = [row["case_id"] for row in report["promoted"]]
    rejected = {row["case_id"]: row["reason"] for row in report["rejected"]}
    assert promoted == ["good"], report
    assert "all-pass" in rejected["dead"], report
    assert "low-reliability" in rejected["unstable"], report
    assert "Promotion Gate" in render(report)
    print("demo OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", nargs="*", type=Path)
    parser.add_argument("--pass-score", type=int, default=4)
    parser.add_argument("--min-spread", type=int, default=2)
    parser.add_argument("--reliability", type=Path)
    parser.add_argument("--oracle", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--promoted-output", type=Path)
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--require-promoted", action="store_true")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo:
        return demo()
    if len(args.traces) < 2:
        parser.error("need at least 2 judged traces or --demo")

    traces = {path.stem.replace("judged_", ""): load(path) for path in args.traces}
    report = analyze(
        traces,
        args.pass_score,
        args.min_spread,
        load_reliability(args.reliability),
        load_oracle(args.oracle),
    )

    print("category dead rates:")
    for category, stats in report["categories"].items():
        print(f"  {category}: dead_rate={stats['dead_rate']:.3f} n={stats['n']}")

    print(f"\npromoted: {len(report['promoted'])}")
    print(f"rejected: {len(report['rejected'])}")
    if report["rejected"]:
        for row in report["rejected"][:50]:
            print(f"  {row['case_id']} ({row['category']}) {row['reason']}")
        if len(report["rejected"]) > 50:
            print(f"  ... {len(report['rejected']) - 50} more")

    if args.json_output:
        write_json(args.json_output, report)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render(report))
    if args.promoted_output:
        if not args.corpus:
            parser.error("--promoted-output requires --corpus")
        write_promoted(args.promoted_output, report, args.corpus)

    if args.require_promoted and not report["promoted"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
