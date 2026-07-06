#!/usr/bin/env python3
"""Fail when repeated judged OpenMythos runs are too unstable."""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


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


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def analyze(
    traces: dict[str, dict[str, dict]],
    max_case_range: int,
    max_avg_range: float,
    max_pass_rate_range: float,
    pass_score: int = 4,
) -> dict:
    common = sorted(set.intersection(*(set(trace) for trace in traces.values())))
    if not common:
        raise SystemExit("No common case_id values across traces")

    runs = {}
    for name, rows in traces.items():
        scores = [rows[case_id]["judge_score"] for case_id in common]
        runs[name] = {
            "avg_score": mean(scores),
            "pass_rate": sum(1 for score in scores if score >= pass_score) / len(scores) * 100,
        }

    unstable = []
    for case_id in common:
        scores = {name: traces[name][case_id]["judge_score"] for name in traces}
        score_range = max(scores.values()) - min(scores.values())
        if score_range > max_case_range:
            unstable.append(
                {
                    "case_id": case_id,
                    "category": next(iter(traces.values()))[case_id].get("category", "unknown"),
                    "range": score_range,
                    "scores": scores,
                }
            )

    avg_values = [run["avg_score"] for run in runs.values()]
    pass_values = [run["pass_rate"] for run in runs.values()]
    avg_range = max(avg_values) - min(avg_values)
    pass_rate_range = max(pass_values) - min(pass_values)
    failed = bool(unstable) or avg_range > max_avg_range or pass_rate_range > max_pass_rate_range

    return {
        "passed": not failed,
        "n_cases": len(common),
        "runs": runs,
        "avg_range": avg_range,
        "pass_rate_range": pass_rate_range,
        "unstable_cases": unstable,
        "thresholds": {
            "max_case_range": max_case_range,
            "max_avg_range": max_avg_range,
            "max_pass_rate_range": max_pass_rate_range,
            "pass_score": pass_score,
        },
    }


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "unknown"


def write_manifest(path: Path, report: dict, trace_paths: list[Path], corpus: Path | None) -> None:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_sha": git_sha(),
        "result": "pass" if report["passed"] else "fail",
        "thresholds": report["thresholds"],
        "n_cases": report["n_cases"],
        "avg_range": report["avg_range"],
        "pass_rate_range": report["pass_rate_range"],
        "unstable_case_ids": [row["case_id"] for row in report["unstable_cases"]],
        "traces": [{"path": str(p), "sha256": sha256(p)} for p in trace_paths],
    }
    if corpus:
        payload["corpus"] = {"path": str(corpus), "sha256": sha256(corpus)}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def print_report(report: dict, limit: int) -> None:
    print(f"cases compared: {report['n_cases']}")
    print(
        "thresholds: "
        f"case_range<={report['thresholds']['max_case_range']} "
        f"avg_range<={report['thresholds']['max_avg_range']} "
        f"pass_rate_range<={report['thresholds']['max_pass_rate_range']}"
    )
    print("\nruns:")
    for name, row in sorted(report["runs"].items()):
        print(f"  {name:<32} avg={row['avg_score']:.3f} pass_rate={row['pass_rate']:.1f}%")
    print(f"\navg score range: {report['avg_range']:.3f}")
    print(f"pass-rate range: {report['pass_rate_range']:.1f}%")

    if report["unstable_cases"]:
        print("\nunstable cases:")
        for row in report["unstable_cases"][:limit]:
            scores = ", ".join(f"{name}={score}" for name, score in sorted(row["scores"].items()))
            print(f"  {row['case_id']} ({row['category']}) range={row['range']} {scores}")
        if len(report["unstable_cases"]) > limit:
            print(f"  ... {len(report['unstable_cases']) - limit} more")

    print("\nOK - reliability gate passed" if report["passed"] else "\nFAILED - reliability gate failed")


def trace_names(paths: list[Path]) -> list[str]:
    counts = {}
    names = []
    for path in paths:
        base = f"{path.parent.name}/{path.stem}"
        counts[base] = counts.get(base, 0) + 1
        names.append(base if counts[base] == 1 else f"{base}#{counts[base]}")
    return names


def demo() -> int:
    stable = {
        "r1": {"a": {"case_id": "a", "category": "x", "judge_score": 4}},
        "r2": {"a": {"case_id": "a", "category": "x", "judge_score": 4}},
    }
    unstable = {
        "r1": {"a": {"case_id": "a", "category": "x", "judge_score": 1}},
        "r2": {"a": {"case_id": "a", "category": "x", "judge_score": 5}},
    }
    assert analyze(stable, 2, 0.5, 100)["passed"]
    assert not analyze(unstable, 2, 5, 100)["passed"]
    print("demo OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", nargs="*", type=Path)
    parser.add_argument("--max-case-range", type=int, default=2)
    parser.add_argument("--max-avg-range", type=float, default=0.5)
    parser.add_argument("--max-pass-rate-range", type=float, default=15.0)
    parser.add_argument("--pass-score", type=int, default=4)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo:
        return demo()
    if len(args.traces) < 2:
        parser.error("need at least 2 judged traces or --demo")

    traces = {name.replace("judged_", ""): load(path) for name, path in zip(trace_names(args.traces), args.traces)}
    report = analyze(
        traces,
        args.max_case_range,
        args.max_avg_range,
        args.max_pass_rate_range,
        args.pass_score,
    )
    print_report(report, args.limit)
    if args.manifest:
        write_manifest(args.manifest, report, args.traces, args.corpus)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
