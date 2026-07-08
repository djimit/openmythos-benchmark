#!/usr/bin/env python3
"""Build gold anchors, judge calibration, and a reliability-weighted leaderboard."""

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def mean(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def load_reliability(path: Path | None) -> dict[str, dict]:
    if not path:
        return {}
    rows = load_jsonl(path)
    return {row["case_id"]: row for row in rows}


def load_trace(path: Path) -> dict[str, dict]:
    return {row["case_id"]: row for row in load_jsonl(path) if "judge_score" in row}


def resolve_trace_path(value: str, repo_root: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def build_anchors(oracle_rows: list[dict], repo_root: Path, pass_score: int) -> list[dict]:
    trace_cache: dict[str, dict[str, dict]] = {}
    anchors = []
    for row in oracle_rows:
        if not row.get("oracle_applicable"):
            continue
        trace = row.get("trace", "")
        trace_rows = trace_cache.setdefault(trace, load_trace(resolve_trace_path(trace, repo_root)))
        judged = trace_rows.get(row["case_id"], {})
        judge_score = judged.get("judge_score")
        judge_pass = int(judge_score) >= pass_score if judge_score is not None else None
        oracle_pass = bool(row.get("oracle_pass"))
        judge_agrees = (judge_pass == oracle_pass) if judge_pass is not None else not row.get("oracle_judge_disagreement")
        anchors.append(
            {
                "case_id": row["case_id"],
                "category": row.get("category", "unknown"),
                "oracle_type": row.get("oracle_type"),
                "oracle_pass": oracle_pass,
                "oracle_confidence": row.get("oracle_confidence", "unknown"),
                "oracle_reason": row.get("oracle_reason"),
                "trace": trace,
                "model": judged.get("model"),
                "judge_model": judged.get("judge_model", trace),
                "judge_score": judge_score,
                "judge_pass": judge_pass,
                "judge_agrees": bool(judge_agrees),
            }
        )
    return anchors


def summarize_anchor_group(rows: list[dict]) -> dict:
    n = len(rows)
    judge_pass = sum(1 for row in rows if row.get("judge_pass"))
    oracle_pass = sum(1 for row in rows if row.get("oracle_pass"))
    false_pass = sum(1 for row in rows if row.get("judge_pass") and not row.get("oracle_pass"))
    false_fail = sum(1 for row in rows if row.get("oracle_pass") and not row.get("judge_pass"))
    agreement = sum(1 for row in rows if row.get("judge_agrees"))
    agreement_rate = agreement / n if n else 0.0
    return {
        "anchors": n,
        "agreement_rate": round(agreement_rate, 3),
        "false_pass_rate": round(false_pass / n, 3) if n else 0.0,
        "false_fail_rate": round(false_fail / n, 3) if n else 0.0,
        "strictness_bias": round((judge_pass / n if n else 0.0) - (oracle_pass / n if n else 0.0), 3),
        "weight": round(max(0.25, agreement_rate), 3),
    }


def calibrate_judges(anchors: list[dict]) -> dict:
    by_judge = defaultdict(list)
    by_judge_category = defaultdict(list)
    for row in anchors:
        judge = row.get("judge_model") or row.get("trace", "unknown")
        by_judge[judge].append(row)
        by_judge_category[(judge, row.get("category", "unknown"))].append(row)

    judges = []
    for judge, rows in sorted(by_judge.items()):
        item = {"judge_model": judge, **summarize_anchor_group(rows)}
        judges.append(item)

    categories = []
    for (judge, category), rows in sorted(by_judge_category.items()):
        categories.append({"judge_model": judge, "category": category, **summarize_anchor_group(rows)})

    return {"anchors": len(anchors), "judges": judges, "categories": categories}


def oracle_case_summary(oracle_rows: list[dict]) -> dict[str, dict]:
    out = defaultdict(lambda: {"oracle_applicable": 0, "oracle_disagreements": 0})
    for row in oracle_rows:
        if not row.get("oracle_applicable"):
            continue
        item = out[row["case_id"]]
        item["oracle_applicable"] += 1
        if row.get("oracle_judge_disagreement"):
            item["oracle_disagreements"] += 1
    return dict(out)


def case_weight(case_id: str, reliability: dict[str, dict], oracle: dict[str, dict]) -> tuple[float, list[str]]:
    weight = 1.0
    flags = []
    if reliability.get(case_id, {}).get("low_reliability"):
        weight *= 0.25
        flags.append("low-reliability")
    if oracle.get(case_id, {}).get("oracle_disagreements", 0):
        weight *= 0.5
        flags.append("oracle-disagreement")
    return weight, flags


def weighted_stats(rows: list[dict], reliability: dict[str, dict], oracle: dict[str, dict], pass_score: int) -> dict:
    weighted_scores = []
    weights = []
    passes = []
    discounted = 0
    low_rel = 0
    oracle_dis = 0
    for row in rows:
        weight, flags = case_weight(row["case_id"], reliability, oracle)
        score = float(row["judge_score"])
        weighted_scores.append(score * weight)
        weights.append(weight)
        passes.append((score >= pass_score) * weight)
        discounted += weight < 1.0
        low_rel += "low-reliability" in flags
        oracle_dis += "oracle-disagreement" in flags

    raw_scores = [float(row["judge_score"]) for row in rows]
    weight_sum = sum(weights)
    weighted_avg = sum(weighted_scores) / weight_sum if weight_sum else 0.0
    weighted_pass = sum(passes) / weight_sum if weight_sum else 0.0
    effective_n = (weight_sum * weight_sum / sum(w * w for w in weights)) if weights and sum(w * w for w in weights) else 0.0
    variance = sum(w * ((float(row["judge_score"]) - weighted_avg) ** 2) for row, w in zip(rows, weights)) / weight_sum if weight_sum else 0.0
    ci95 = 1.96 * math.sqrt(variance / effective_n) if effective_n else 0.0
    return {
        "raw_avg_score": round(mean(raw_scores), 3),
        "raw_pass_rate": round(sum(1 for score in raw_scores if score >= pass_score) / len(raw_scores), 3) if raw_scores else 0.0,
        "weighted_avg_score": round(weighted_avg, 3),
        "weighted_pass_rate": round(weighted_pass, 3),
        "ci95": round(ci95, 3),
        "cases": len(rows),
        "effective_cases": round(effective_n, 1),
        "avg_case_weight": round(mean(weights), 3),
        "discounted_cases": discounted,
        "low_reliability_cases": low_rel,
        "oracle_disagreement_cases": oracle_dis,
    }


def model_name(path: Path, rows: list[dict]) -> str:
    return rows[0].get("model") if rows else path.stem.replace("judged_", "")


def build_leaderboard(paths: list[Path], reliability: dict[str, dict], oracle: dict[str, dict], pass_score: int) -> dict:
    models = []
    traces = {}
    for path in paths:
        rows = [row for row in load_jsonl(path) if "judge_score" in row]
        model = model_name(path, rows)
        traces[model] = {row["case_id"]: row for row in rows}
        models.append({"model": model, "trace": str(path), **weighted_stats(rows, reliability, oracle, pass_score)})

    common = sorted(set.intersection(*(set(rows) for rows in traces.values()))) if traces else []
    common_scores = {
        model: weighted_stats([rows[case_id] for case_id in common], reliability, oracle, pass_score)["weighted_avg_score"]
        for model, rows in traces.items()
    }
    return {
        "models": sorted(models, key=lambda row: (-row["weighted_avg_score"], -row["weighted_pass_rate"], row["model"])),
        "benchmark": {
            "common_cases": len(common),
            "weighted_discrimination": round(max(common_scores.values()) - min(common_scores.values()), 3) if common_scores else 0.0,
            "avg_case_weight": round(mean(case_weight(case_id, reliability, oracle)[0] for case_id in common), 3),
        },
    }


def render(report: dict) -> str:
    lines = [
        "# OpenMythos Calibrated Leaderboard",
        "",
        f"- gold anchors: `{report['calibration']['anchors']}`",
        f"- common cases: `{report['leaderboard']['benchmark']['common_cases']}`",
        f"- weighted discrimination: `{report['leaderboard']['benchmark']['weighted_discrimination']}`",
        f"- avg case weight: `{report['leaderboard']['benchmark']['avg_case_weight']}`",
        "",
        "## Leaderboard",
        "",
        "| rank | model | weighted avg | raw avg | weighted pass | raw pass | ci95 | effective cases | discounted |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(report["leaderboard"]["models"], 1):
        lines.append(
            f"| {rank} | {row['model']} | {row['weighted_avg_score']:.3f} | {row['raw_avg_score']:.3f} | "
            f"{row['weighted_pass_rate']:.3f} | {row['raw_pass_rate']:.3f} | {row['ci95']:.3f} | "
            f"{row['effective_cases']:.1f} | {row['discounted_cases']} |"
        )

    lines.extend(["", "## Judge Calibration", "", "| judge | anchors | agreement | false pass | false fail | bias | weight |", "|---|---:|---:|---:|---:|---:|---:|"])
    for row in report["calibration"]["judges"]:
        lines.append(
            f"| {row['judge_model']} | {row['anchors']} | {row['agreement_rate']:.3f} | "
            f"{row['false_pass_rate']:.3f} | {row['false_fail_rate']:.3f} | "
            f"{row['strictness_bias']:+.3f} | {row['weight']:.3f} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def demo() -> int:
    anchors = [
        {"judge_model": "strict", "category": "canary", "oracle_pass": True, "judge_pass": False, "judge_agrees": False},
        {"judge_model": "strict", "category": "canary", "oracle_pass": False, "judge_pass": False, "judge_agrees": True},
    ]
    calibration = calibrate_judges(anchors)
    assert calibration["judges"][0]["agreement_rate"] == 0.5, calibration
    reliability = {"a": {"low_reliability": True}}
    oracle = {"a": {"oracle_disagreements": 1}}
    assert case_weight("a", reliability, oracle) == (0.125, ["low-reliability", "oracle-disagreement"])
    print("demo OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", nargs="*", type=Path)
    parser.add_argument("--oracle", type=Path)
    parser.add_argument("--reliability", type=Path)
    parser.add_argument("--pass-score", type=int, default=4)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--anchors-output", type=Path)
    parser.add_argument("--judge-output", type=Path)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo:
        return demo()
    if len(args.traces) < 2:
        parser.error("need at least 2 judged traces or --demo")
    if not args.oracle:
        parser.error("--oracle is required")

    oracle_rows = load_jsonl(args.oracle)
    reliability = load_reliability(args.reliability)
    oracle_summary = oracle_case_summary(oracle_rows)
    anchors = build_anchors(oracle_rows, REPO_ROOT, args.pass_score)
    calibration = calibrate_judges(anchors)
    leaderboard = build_leaderboard(args.traces, reliability, oracle_summary, args.pass_score)
    report = {"calibration": calibration, "leaderboard": leaderboard}

    if args.anchors_output:
        write_jsonl(args.anchors_output, anchors)
    if args.judge_output:
        write_json(args.judge_output, calibration)
    if args.json_output:
        write_json(args.json_output, report)
    markdown = render(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown)
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
