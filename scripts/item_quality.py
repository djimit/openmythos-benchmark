#!/usr/bin/env python3
"""Rank OpenMythos cases by measured item quality across judged traces."""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise SystemExit(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def load_trace(path: Path) -> dict[str, dict]:
    rows = {}
    for row in load_jsonl(path):
        if "judge_score" not in row:
            raise SystemExit(f"{path} is missing judge_score")
        rows[row["case_id"]] = row
    return rows


def load_oracle(path: Path | None) -> dict[str, dict]:
    if not path:
        return {}
    by_case = {}
    for row in load_jsonl(path):
        case = by_case.setdefault(
            row["case_id"],
            {"oracle_applicable": False, "oracle_failures": 0, "oracle_disagreements": 0},
        )
        if row.get("oracle_applicable"):
            case["oracle_applicable"] = True
            if row.get("oracle_pass") is False:
                case["oracle_failures"] += 1
            if row.get("oracle_judge_disagreement"):
                case["oracle_disagreements"] += 1
    return by_case


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def analyze(traces: dict[str, dict[str, dict]], oracle: dict[str, dict] | None = None, pass_score: int = 4) -> list[dict]:
    oracle = oracle or {}
    common = sorted(set.intersection(*(set(trace) for trace in traces.values())))
    if not common:
        raise SystemExit("No common case_id values across traces")

    rows = []
    for case_id in common:
        case_rows = [trace[case_id] for trace in traces.values()]
        scores = [int(row["judge_score"]) for row in case_rows]
        latencies = [float(row.get("latency_ms", 0) or 0) for row in case_rows]
        tokens = [float(row.get("tokens", 0) or 0) for row in case_rows]
        spread = max(scores) - min(scores)
        pass_rate = sum(1 for score in scores if score >= pass_score) / len(scores)
        dead = max(scores) == min(scores)
        oracle_row = oracle.get(case_id, {})
        cost_penalty = min(mean(latencies) / 10000, 1.0) + min(mean(tokens) / 1000, 1.0)
        dead_penalty = 3.0 if dead else 0.0
        disagreement_penalty = 2.0 if oracle_row.get("oracle_disagreements") else 0.0
        quality_score = spread - dead_penalty - disagreement_penalty - cost_penalty
        label = label_case(scores, spread, pass_rate, dead, oracle_row)
        rows.append(
            {
                "case_id": case_id,
                "category": case_rows[0].get("category", "unknown"),
                "mean_score": round(mean(scores), 3),
                "pass_rate": round(pass_rate, 3),
                "spread": spread,
                "dead": dead,
                "instability": 0,
                "oracle_applicable": bool(oracle_row.get("oracle_applicable")),
                "oracle_failures": int(oracle_row.get("oracle_failures", 0)),
                "oracle_judge_disagreement": int(oracle_row.get("oracle_disagreements", 0)),
                "avg_latency_ms": round(mean(latencies), 1),
                "avg_tokens": round(mean(tokens), 1),
                "quality_score": round(quality_score, 3),
                "label": label,
            }
        )
    return sorted(rows, key=lambda row: (row["label"] != "promote-candidate", -row["quality_score"], row["case_id"]))


def label_case(scores: list[int], spread: int, pass_rate: float, dead: bool, oracle: dict) -> str:
    if oracle.get("oracle_disagreements"):
        return "quarantine"
    if dead:
        return "replace" if pass_rate in {0.0, 1.0} else "rewrite"
    if spread >= 3 and max(scores) >= 4 and min(scores) <= 2:
        return "promote-candidate"
    if spread <= 1:
        return "rewrite"
    return "keep"


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")


def print_report(rows: list[dict], limit: int) -> None:
    counts = Counter(row["label"] for row in rows)
    print(f"cases={len(rows)}")
    for label, count in sorted(counts.items()):
        print(f"  {label}: {count}")
    print("\ntop cases:")
    for row in rows[:limit]:
        print(
            f"  {row['case_id']} {row['label']} score={row['quality_score']:.3f} "
            f"spread={row['spread']} pass_rate={row['pass_rate']:.3f} dead={row['dead']}"
        )


def trace_names(paths: list[Path]) -> list[str]:
    counts = {}
    names = []
    for path in paths:
        base = f"{path.parent.name}/{path.stem.replace('judged_', '')}"
        counts[base] = counts.get(base, 0) + 1
        names.append(base if counts[base] == 1 else f"{base}#{counts[base]}")
    return names


def demo() -> int:
    rows = analyze(
        {
            "weak": {
                "good": {"case_id": "good", "category": "x", "judge_score": 1},
                "dead": {"case_id": "dead", "category": "x", "judge_score": 5},
            },
            "strong": {
                "good": {"case_id": "good", "category": "x", "judge_score": 5},
                "dead": {"case_id": "dead", "category": "x", "judge_score": 5},
            },
        }
    )
    by_id = {row["case_id"]: row for row in rows}
    assert by_id["good"]["label"] == "promote-candidate", rows
    assert by_id["dead"]["label"] == "replace", rows
    assert by_id["good"]["quality_score"] > by_id["dead"]["quality_score"], rows
    print("demo OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", nargs="*", type=Path)
    parser.add_argument("--oracle-output", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--pass-score", type=int, default=4)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo:
        return demo()
    if len(args.traces) < 2:
        parser.error("need at least 2 judged traces or --demo")

    traces = {name: load_trace(path) for name, path in zip(trace_names(args.traces), args.traces)}
    rows = analyze(traces, load_oracle(args.oracle_output), args.pass_score)
    print_report(rows, args.limit)
    if args.output:
        write_jsonl(args.output, rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
