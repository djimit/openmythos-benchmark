#!/usr/bin/env python3
"""Fail when OpenMythos traces exceed operational error, latency, or token budgets."""

import argparse
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def load(paths: list[Path]) -> list[dict]:
    rows = []
    for path in paths:
        with path.open() as f:
            for line in f:
                if line.strip():
                    row = json.loads(line)
                    row["_trace"] = str(path)
                    rows.append(row)
    return rows


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def is_error(row: dict) -> bool:
    return str(row.get("response", "")).startswith("ERROR:")


def summarize(rows: list[dict]) -> dict:
    if not rows:
        raise SystemExit("No rows found in traces")

    categories = defaultdict(list)
    for row in rows:
        categories[row.get("category", "unknown")].append(row)

    def summary(items: list[dict]) -> dict:
        latencies = [float(row.get("latency_ms", 0) or 0) for row in items]
        tokens = [float(row.get("tokens", 0) or 0) for row in items]
        errors = [row for row in items if is_error(row)]
        return {
            "cases": len(items),
            "errors": len(errors),
            "error_rate": len(errors) / len(items) * 100,
            "avg_latency_ms": mean(latencies),
            "max_latency_ms": max(latencies),
            "avg_tokens": mean(tokens),
            "max_tokens": max(tokens),
        }

    return {
        "overall": summary(rows),
        "categories": {cat: summary(items) for cat, items in sorted(categories.items())},
        "errors": [row for row in rows if is_error(row)],
        "slowest": sorted(rows, key=lambda row: float(row.get("latency_ms", 0) or 0), reverse=True),
        "largest": sorted(rows, key=lambda row: float(row.get("tokens", 0) or 0), reverse=True),
    }


def analyze(rows: list[dict], thresholds: dict) -> dict:
    report = summarize(rows)
    overall = report["overall"]
    failures = []

    checks = [
        ("max_error_rate", "error_rate", "error rate", "%"),
        ("max_avg_latency_ms", "avg_latency_ms", "avg latency", "ms"),
        ("max_max_latency_ms", "max_latency_ms", "max latency", "ms"),
        ("max_avg_tokens", "avg_tokens", "avg tokens", ""),
        ("max_max_tokens", "max_tokens", "max tokens", ""),
    ]
    for arg_name, metric, label, unit in checks:
        limit = thresholds.get(arg_name)
        if limit is not None and overall[metric] > limit:
            failures.append(
                {
                    "threshold": arg_name,
                    "metric": label,
                    "actual": overall[metric],
                    "limit": limit,
                    "unit": unit,
                }
            )

    report["thresholds"] = thresholds
    report["failures"] = failures
    report["passed"] = not failures
    return report


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
        "overall": report["overall"],
        "failures": report["failures"],
        "traces": [{"path": str(p), "sha256": sha256(p)} for p in trace_paths],
    }
    if corpus:
        payload["corpus"] = {"path": str(corpus), "sha256": sha256(corpus)}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def print_report(report: dict, limit: int) -> None:
    overall = report["overall"]
    print(
        f"cases={overall['cases']} errors={overall['errors']} "
        f"error_rate={overall['error_rate']:.1f}%"
    )
    print(
        f"latency avg={overall['avg_latency_ms']:.1f}ms "
        f"max={overall['max_latency_ms']:.1f}ms"
    )
    print(f"tokens avg={overall['avg_tokens']:.1f} max={overall['max_tokens']:.1f}")

    print("\ncategory summary:")
    for category, row in report["categories"].items():
        print(
            f"  {category:<22} n={row['cases']} errors={row['errors']} "
            f"avg_ms={row['avg_latency_ms']:.1f} avg_tokens={row['avg_tokens']:.1f}"
        )

    if report["failures"]:
        print("\nfailures:")
        for failure in report["failures"]:
            print(
                f"  {failure['metric']}: {failure['actual']:.1f}{failure['unit']} "
                f"> {failure['limit']}{failure['unit']}"
            )

    offender_rows = []
    failed_thresholds = {failure["threshold"] for failure in report["failures"]}
    if report["errors"]:
        offender_rows.extend(report["errors"])
    if failed_thresholds & {"max_avg_latency_ms", "max_max_latency_ms"}:
        offender_rows.extend(report["slowest"][:limit])
    if failed_thresholds & {"max_avg_tokens", "max_max_tokens"}:
        offender_rows.extend(report["largest"][:limit])
    if not offender_rows:
        offender_rows = report["slowest"][:limit]

    seen = set()
    offenders = []
    for row in offender_rows:
        key = (row.get("_trace"), row.get("case_id"))
        if key not in seen:
            seen.add(key)
            offenders.append(row)

    if offenders:
        print("\noffenders:")
        for row in offenders[:limit]:
            print(
                f"  {row.get('case_id', '?')} ({row.get('category', 'unknown')}) "
                f"latency={float(row.get('latency_ms', 0) or 0):.1f}ms "
                f"tokens={float(row.get('tokens', 0) or 0):.1f}"
            )

    print("\nOK - operational gate passed" if report["passed"] else "\nFAILED - operational gate failed")


def demo() -> int:
    rows = [
        {"case_id": "fast", "category": "x", "response": "ok", "latency_ms": 100, "tokens": 10},
        {"case_id": "slow", "category": "x", "response": "ok", "latency_ms": 900, "tokens": 90},
        {"case_id": "err", "category": "y", "response": "ERROR: timeout", "latency_ms": 0, "tokens": 0},
    ]
    assert analyze(rows[:2], {"max_error_rate": 0, "max_avg_latency_ms": 600})["passed"]
    assert not analyze(rows, {"max_error_rate": 0, "max_avg_latency_ms": 600})["passed"]
    print("demo OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", nargs="*", type=Path)
    parser.add_argument("--max-error-rate", type=float, default=0.0)
    parser.add_argument("--max-avg-latency-ms", type=float)
    parser.add_argument("--max-max-latency-ms", type=float)
    parser.add_argument("--max-avg-tokens", type=float)
    parser.add_argument("--max-max-tokens", type=float)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo:
        return demo()
    if not args.traces:
        parser.error("need at least 1 trace or --demo")

    thresholds = {
        "max_error_rate": args.max_error_rate,
        "max_avg_latency_ms": args.max_avg_latency_ms,
        "max_max_latency_ms": args.max_max_latency_ms,
        "max_avg_tokens": args.max_avg_tokens,
        "max_max_tokens": args.max_max_tokens,
    }
    report = analyze(load(args.traces), thresholds)
    print_report(report, args.limit)
    if args.manifest:
        write_manifest(args.manifest, report, args.traces, args.corpus)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
