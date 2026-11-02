#!/usr/bin/env python3
"""Fail when repeated judged OpenMythos runs are too unstable."""

import argparse
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
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


def require_one_rubric(traces: dict[str, dict[str, dict]]) -> str:
    versions = {
        row.get("judge_rubric_version")
        for rows in traces.values()
        for row in rows.values()
    }
    if None in versions or len(versions) != 1:
        raise SystemExit(f"judged traces must use one explicit rubric version: {versions}")
    return versions.pop()


def mean(values: list[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def reliability_rows(
    traces: dict[str, dict[str, dict]],
    max_case_range: int,
    pass_score: int,
) -> list[dict]:
    common = sorted(set.intersection(*(set(trace) for trace in traces.values())))
    if not common:
        raise SystemExit("No common case_id values across traces")

    rows = []
    for case_id in common:
        scores = {name: traces[name][case_id]["judge_score"] for name in traces}
        values = list(scores.values())
        passes = {name: score >= pass_score for name, score in scores.items()}
        responses = {traces[name][case_id].get("response", "") for name in traces}
        pass_votes = sum(passes.values())
        score_range = max(values) - min(values)
        pass_disagreement = 0 < pass_votes < len(passes)
        low_reliability = score_range > max_case_range or pass_disagreement
        category = next(iter(traces.values()))[case_id].get("category", "unknown")
        rows.append(
            {
                "case_id": case_id,
                "category": category,
                "scores": scores,
                "score_range": score_range,
                "avg_score": round(mean(values), 3),
                "pass_votes": pass_votes,
                "judge_count": len(passes),
                "pass_disagreement": pass_disagreement,
                "exact_response_agreement": len(responses) == 1,
                "low_reliability": low_reliability,
            }
        )
    return rows


def category_rows(cases: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for row in cases:
        grouped[row["category"]].append(row)
    out = []
    for category, rows in sorted(grouped.items()):
        out.append(
            {
                "category": category,
                "cases": len(rows),
                "low_reliability": sum(1 for row in rows if row["low_reliability"]),
                "instability_rate": round(
                    sum(1 for row in rows if row["low_reliability"]) / len(rows), 3
                ),
                "avg_score_range": round(mean(row["score_range"] for row in rows), 3),
                "pass_disagreement_rate": round(
                    sum(1 for row in rows if row["pass_disagreement"]) / len(rows), 3
                ),
            }
        )
    return sorted(out, key=lambda row: (-row["instability_rate"], row["category"]))


def analyze(
    traces: dict[str, dict[str, dict]],
    max_case_range: int,
    max_avg_range: float,
    max_pass_rate_range: float,
    pass_score: int = 4,
) -> dict:
    cases = reliability_rows(traces, max_case_range, pass_score)
    common = [row["case_id"] for row in cases]

    runs = {}
    for name, rows in traces.items():
        scores = [rows[case_id]["judge_score"] for case_id in common]
        runs[name] = {
            "avg_score": mean(scores),
            "pass_rate": sum(1 for score in scores if score >= pass_score) / len(scores) * 100,
        }

    unstable = [row for row in cases if row["low_reliability"]]

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
        "exact_response_agreement_rate": sum(row["exact_response_agreement"] for row in cases) / len(cases),
        "unstable_cases": unstable,
        "cases": cases,
        "categories": category_rows(cases),
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


def write_manifest(path: Path, report: dict, trace_paths: list[Path], corpus: Path | None, oracle: Path | None = None) -> None:
    trace_evidence = []
    for trace_path in trace_paths:
        first = next((json.loads(line) for line in trace_path.read_text().splitlines() if line.strip()), {})
        trace_evidence.append({
            "path": str(trace_path),
            "sha256": sha256(trace_path),
            "model": first.get("model"),
            "model_digest": first.get("model_digest"),
            "judge_model": first.get("judge_model"),
            "judge_digest": first.get("judge_digest"),
            "judge_rubric_version": first.get("judge_rubric_version"),
            "generation_options": first.get("generation_options"),
        })
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_sha": git_sha(),
        "result": "pass" if report["passed"] else "fail",
        "thresholds": report["thresholds"],
        "n_cases": report["n_cases"],
        "avg_range": report["avg_range"],
        "pass_rate_range": report["pass_rate_range"],
        "unstable_case_ids": [row["case_id"] for row in report["unstable_cases"]],
        "case_ids": [row["case_id"] for row in report["cases"]],
        "exact_response_agreement_rate": report["exact_response_agreement_rate"],
        "traces": trace_evidence,
    }
    if corpus:
        payload["corpus"] = {"path": str(corpus), "sha256": sha256(corpus)}
    if oracle:
        rows = [json.loads(line) for line in oracle.read_text().splitlines() if line.strip()]
        payload["oracle"] = {
            "path": str(oracle), "sha256": sha256(oracle),
            "applicable_cases": len({row["case_id"] for row in rows if row.get("oracle_applicable")}),
            "judge_disagreements": sum(bool(row.get("oracle_judge_disagreement")) for row in rows),
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def write_json(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")


def render_markdown(report: dict, limit: int) -> str:
    lines = [
        "# OpenMythos Judge Reliability",
        "",
        f"- cases compared: `{report['n_cases']}`",
        f"- avg score range: `{report['avg_range']:.3f}`",
        f"- pass-rate range: `{report['pass_rate_range']:.1f}%`",
        f"- exact response agreement: `{report['exact_response_agreement_rate']:.1%}`",
        f"- low-reliability cases: `{len(report['unstable_cases'])}`",
        "",
        "## Runs",
        "",
        "| run | avg score | pass rate |",
        "|---|---:|---:|",
    ]
    for name, row in sorted(report["runs"].items()):
        lines.append(f"| {name} | {row['avg_score']:.3f} | {row['pass_rate']:.1f}% |")

    lines.extend(
        [
            "",
            "## Category Instability",
            "",
            "| category | cases | low reliability | instability | avg score range | pass disagreement |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in report["categories"]:
        lines.append(
            f"| {row['category']} | {row['cases']} | {row['low_reliability']} | "
            f"{row['instability_rate']:.3f} | {row['avg_score_range']:.3f} | "
            f"{row['pass_disagreement_rate']:.3f} |"
        )

    lines.extend(
        [
            "",
            f"## Top {limit} Low-Reliability Cases",
            "",
            "| case | category | range | pass votes | scores |",
            "|---|---|---:|---:|---|",
        ]
    )
    ranked = sorted(
        report["unstable_cases"],
        key=lambda row: (-row["score_range"], row["case_id"]),
    )
    for row in ranked[:limit]:
        scores = ", ".join(f"{name}={score}" for name, score in sorted(row["scores"].items()))
        lines.append(
            f"| {row['case_id']} | {row['category']} | {row['score_range']} | "
            f"{row['pass_votes']}/{row['judge_count']} | {scores} |"
        )
    lines.append("")
    return "\n".join(lines)


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
    print(f"exact response agreement: {report['exact_response_agreement_rate']:.1%}")

    if report["unstable_cases"]:
        print("\nunstable cases:")
        for row in report["unstable_cases"][:limit]:
            scores = ", ".join(f"{name}={score}" for name, score in sorted(row["scores"].items()))
            print(f"  {row['case_id']} ({row['category']}) range={row['score_range']} {scores}")
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
    split_pass = {
        "r1": {"a": {"case_id": "a", "category": "x", "judge_score": 3}},
        "r2": {"a": {"case_id": "a", "category": "x", "judge_score": 4}},
    }
    assert analyze(stable, 2, 0.5, 100)["passed"]
    assert not analyze(unstable, 2, 5, 100)["passed"]
    report = analyze(split_pass, 2, 5, 100)
    assert report["unstable_cases"][0]["pass_disagreement"], report
    assert "Category Instability" in render_markdown(report, 5)
    print("demo OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", nargs="*", type=Path)
    parser.add_argument("--max-case-range", type=int, default=2)
    parser.add_argument("--max-avg-range", type=float, default=0.5)
    parser.add_argument("--max-pass-rate-range", type=float, default=15.0)
    parser.add_argument("--pass-score", type=int, default=4)
    parser.add_argument("--min-runs", type=int, default=3)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--case-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--oracle", type=Path)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo:
        return demo()
    if len(args.traces) < args.min_runs:
        parser.error(f"need at least {args.min_runs} judged traces or --demo")

    traces = {name.replace("judged_", ""): load(path) for name, path in zip(trace_names(args.traces), args.traces)}
    require_one_rubric(traces)
    report = analyze(
        traces,
        args.max_case_range,
        args.max_avg_range,
        args.max_pass_rate_range,
        args.pass_score,
    )
    print_report(report, args.limit)
    if args.manifest:
        write_manifest(args.manifest, report, args.traces, args.corpus, args.oracle)
    if args.json_output:
        write_json(args.json_output, report)
    if args.case_output:
        write_jsonl(args.case_output, report["cases"])
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(report, args.limit))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
