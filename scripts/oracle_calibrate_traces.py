#!/usr/bin/env python3
"""Calibrate judged traces with high-confidence deterministic oracle evidence."""

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
REPORT_DIR = REPO_ROOT / "analysis" / "openmythos-apex-runs" / "reports"
TRACE_DIR = REPO_ROOT / "traces" / "apex-r15-oracle-calibrated"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def oracle_index(path: Path) -> dict[tuple[str, str], dict]:
    rows = load_jsonl(path)
    return {(row["trace"], row["case_id"]): row for row in rows}


def calibrate_row(row: dict, oracle: dict | None) -> dict:
    out = dict(row)
    out["original_judge_score"] = row["judge_score"]
    out["original_judge_model"] = row.get("judge_model")
    if oracle and oracle.get("oracle_confidence") == "high" and oracle.get("oracle_applicable"):
        out["judge_score"] = 4 if oracle.get("oracle_pass") else 2
        out["judge_model"] = "oracle-calibrated"
        out["judge_reason"] = oracle.get("oracle_reason", "deterministic oracle calibration")
        out["oracle_calibrated"] = True
        out["oracle_pass"] = oracle.get("oracle_pass")
        out["oracle_type"] = oracle.get("oracle_type")
    else:
        out["oracle_calibrated"] = False
    return out


def demo() -> int:
    row = {"case_id": "a", "judge_score": 3, "judge_model": "judge"}
    passed = calibrate_row(row, {"oracle_applicable": True, "oracle_confidence": "high", "oracle_pass": True})
    failed = calibrate_row(row, {"oracle_applicable": True, "oracle_confidence": "high", "oracle_pass": False})
    assert passed["judge_score"] == 4 and passed["original_judge_score"] == 3, passed
    assert failed["judge_score"] == 2 and failed["oracle_calibrated"], failed
    print("demo OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", nargs="*", type=Path)
    parser.add_argument("--oracle", type=Path, default=REPORT_DIR / "apex-r14-oracle-overlay.jsonl")
    parser.add_argument("--output-dir", type=Path, default=TRACE_DIR)
    parser.add_argument("--summary", type=Path, default=REPORT_DIR / "apex-r15-oracle-calibration-summary.json")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo:
        return demo()
    if not args.traces:
        parser.error("need at least one judged trace or --demo")

    oracle = oracle_index(args.oracle)
    summary = {"traces": [], "rows": 0, "calibrated": 0, "pass_to_score4": 0, "fail_to_score2": 0}
    for trace in args.traces:
        rows = []
        for row in load_jsonl(trace):
            o = oracle.get((str(trace), row["case_id"]))
            calibrated = calibrate_row(row, o)
            rows.append(calibrated)
            summary["rows"] += 1
            if calibrated["oracle_calibrated"]:
                summary["calibrated"] += 1
                summary["pass_to_score4"] += calibrated["judge_score"] == 4
                summary["fail_to_score2"] += calibrated["judge_score"] == 2
        out = args.output_dir / trace.name.replace("judged_", "calibrated_")
        write_jsonl(out, rows)
        summary["traces"].append({"input": str(trace), "output": str(out), "rows": len(rows)})

    write_json(args.summary, summary)
    print(f"Wrote {args.summary}")
    for row in summary["traces"]:
        print(f"Wrote {row['output']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
