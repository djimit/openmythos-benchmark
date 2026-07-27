#!/usr/bin/env python3
"""Gate Pipeline — end-to-end model promotion through all gates.

Runs in order:
1. operational_gate.py — SLO/latency/error budget check
2. regression_gate.py — no degradation vs baseline
3. promotion_gate.py — spread + discrimination quality
4. spec_compliance_gate.py — DDD artifact completeness (Constitution v1.2.0 Article VI)

Usage:
    python3 gate_pipeline.py --baseline traces/baseline/ --candidate traces/candidate/ --corpus cases/corpus.jsonl
    python3 gate_pipeline.py --specs-dir /path/to/project/specs/ --change-type greenfield
    python3 gate_pipeline.py --demo
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SCRIPTS = REPO_ROOT / "scripts"


def run_spec_compliance_gate(
    specs_dir: Path, change_type: str = "greenfield", thresholds: dict | None = None
) -> tuple[bool, dict]:
    """Run DDD spec compliance gate on project /specs folder."""
    cmd = [
        sys.executable,
        str(SCRIPTS / "spec_compliance_gate.py"),
        "--specs-dir",
        str(specs_dir),
        "--change-type",
        change_type,
    ]
    if thresholds:
        if thresholds.get("min_terms"):
            cmd.extend(["--min-terms", str(thresholds["min_terms"])])

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    passed = result.returncode == 0

    return passed, {
        "gate": "spec_compliance",
        "passed": passed,
        "stdout": result.stdout[-500:] if result.stdout else "",
        "stderr": result.stderr[-500:] if result.stderr else "",
    }


def run_operational_gate(traces: list[Path], thresholds: dict) -> tuple[bool, dict]:
    """Run operational gate on candidate traces."""
    cmd = [sys.executable, str(SCRIPTS / "operational_gate.py")]
    cmd.extend(str(t) for t in traces)

    if thresholds.get("max_error_rate") is not None:
        cmd.extend(["--max-error-rate", str(thresholds["max_error_rate"])])
    if thresholds.get("max_avg_latency_ms") is not None:
        cmd.extend(["--max-avg-latency-ms", str(thresholds["max_avg_latency_ms"])])
    if thresholds.get("max_max_latency_ms") is not None:
        cmd.extend(["--max-max-latency-ms", str(thresholds["max_max_latency_ms"])])

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    passed = result.returncode == 0

    return passed, {
        "gate": "operational",
        "passed": passed,
        "stdout": result.stdout[-500:] if result.stdout else "",
        "stderr": result.stderr[-500:] if result.stderr else "",
    }


def run_regression_gate(
    baseline: Path, candidate: Path, allow_category_regression: bool = False
) -> tuple[bool, dict]:
    """Run regression gate comparing baseline vs candidate."""
    cmd = [
        sys.executable,
        str(SCRIPTS / "regression_gate.py"),
        "--baseline",
        str(baseline),
        "--candidate",
        str(candidate),
    ]
    if allow_category_regression:
        cmd.append("--allow-category-regression")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    passed = result.returncode == 0

    return passed, {
        "gate": "regression",
        "passed": passed,
        "stdout": result.stdout[-500:] if result.stdout else "",
        "stderr": result.stderr[-500:] if result.stderr else "",
    }


def run_promotion_gate(
    tracedirs: list[Path], corpus: Path, min_spread: int = 2, pass_score: int = 4
) -> tuple[bool, dict]:
    """Run promotion gate on judged traces from multiple models."""
    # Find judged traces in each directory
    judged = []
    for d in tracedirs:
        judged_files = list(d.glob("judged_*.jsonl"))
        judged.extend(judged_files)

    if len(judged) < 2:
        return False, {
            "gate": "promotion",
            "passed": False,
            "reason": f"need at least 2 judged traces, found {len(judged)}",
        }

    cmd = [
        sys.executable,
        str(SCRIPTS / "promotion_gate.py"),
        "--corpus",
        str(corpus),
        "--min-spread",
        str(min_spread),
        "--pass-score",
        str(pass_score),
        "--require-promoted",
    ]
    cmd.extend(str(t) for t in judged)

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    passed = result.returncode == 0

    return passed, {
        "gate": "promotion",
        "passed": passed,
        "stdout": result.stdout[-500:] if result.stdout else "",
        "stderr": result.stderr[-500:] if result.stderr else "",
    }


def run_pipeline(
    candidate_traces: list[Path],
    baseline_traces: list[Path] | None = None,
    corpus: Path | None = None,
    thresholds: dict | None = None,
    gates: list[str] | None = None,
    specs_dir: Path | None = None,
    change_type: str = "greenfield",
) -> dict:
    """Run full pipeline. Stops at first failure."""
    gates = gates or ["operational", "regression", "promotion", "spec_compliance"]
    thresholds = thresholds or {}
    results = {"gates": [], "overall": "pending", "stopped_at": None}

    for gate in gates:
        if gate == "operational":
            passed, detail = run_operational_gate(candidate_traces, thresholds)
        elif gate == "regression":
            if not baseline_traces:
                results["gates"].append(
                    {"gate": "regression", "passed": None, "skipped": True}
                )
                continue
            # Compare first baseline vs first candidate (simplified)
            passed, detail = run_regression_gate(
                baseline_traces[0], candidate_traces[0]
            )
        elif gate == "promotion":
            if not corpus:
                results["gates"].append(
                    {"gate": "promotion", "passed": None, "skipped": True}
                )
                continue
            all_traces = candidate_traces + (baseline_traces or [])
            # Group by directory for promotion gate
            dirs = list(set(t.parent for t in all_traces))
            passed, detail = run_promotion_gate(dirs, corpus)
        elif gate == "spec_compliance":
            if not specs_dir:
                results["gates"].append(
                    {"gate": "spec_compliance", "passed": None, "skipped": True}
                )
                continue
            gate_thresholds = thresholds.get("spec_compliance", {})
            passed, detail = run_spec_compliance_gate(
                specs_dir, change_type, gate_thresholds
            )
        else:
            continue

        results["gates"].append(detail)

        if not passed:
            results["overall"] = "rejected"
            results["stopped_at"] = gate
            return results

    results["overall"] = "approved"
    return results


def render_report(results: dict) -> str:
    """Format pipeline results as markdown."""
    lines = [
        "# Gate Pipeline Report",
        "",
        f"**Overall: {results['overall'].upper()}**",
        "",
        "## Gate Results",
        "",
        "| gate | result |",
        "|------|--------|",
    ]
    for gate in results["gates"]:
        if gate.get("skipped"):
            result = "SKIPPED"
        elif gate["passed"]:
            result = "PASS"
        else:
            result = "FAIL"
        lines.append(f"| {gate['gate']} | {result} |")

    if results.get("stopped_at"):
        lines.extend(["", f"**Pipeline stopped at: {results['stopped_at']}**"])

    lines.append("")
    return "\n".join(lines)


def demo() -> int:
    """Self-check: verify pipeline structure without running actual gates."""
    # Verify all gate scripts exist
    required = ["operational_gate.py", "regression_gate.py", "promotion_gate.py", "spec_compliance_gate.py"]
    for script in required:
        path = SCRIPTS / script
        assert path.exists(), f"missing {script}"

    # Verify pipeline logic with mock results
    results = {
        "gates": [
            {"gate": "operational", "passed": True},
            {"gate": "regression", "passed": True},
            {"gate": "promotion", "passed": True},
        ],
        "overall": "approved",
    }
    report = render_report(results)
    assert "PASS" in report

    # Test early stop
    results_fail = {
        "gates": [
            {"gate": "operational", "passed": True},
            {"gate": "regression", "passed": False},
        ],
        "overall": "rejected",
        "stopped_at": "regression",
    }
    report_fail = render_report(results_fail)
    assert "FAIL" in report_fail
    assert "stopped" in report_fail

    print("gate_pipeline demo OK")
    print(f"  Gates: {', '.join(required)}")
    print(f"  Report format: OK")
    print(f"  Early-stop logic: OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate", type=Path, nargs="+", help="Candidate trace files"
    )
    parser.add_argument("--baseline", type=Path, nargs="+", help="Baseline trace files")
    parser.add_argument("--corpus", type=Path, help="Corpus file for promotion gate")
    parser.add_argument(
        "--gates",
        nargs="+",
        default=["operational", "regression", "promotion"],
        help="Gates to run (in order)",
    )
    parser.add_argument("--max-error-rate", type=float, default=0.0)
    parser.add_argument("--max-avg-latency-ms", type=float)
    parser.add_argument("--max-max-latency-ms", type=float)
    parser.add_argument("--output", type=Path, help="Write report to file")
    parser.add_argument("--specs-dir", type=Path, help="Project /specs directory for DDD compliance gate")
    parser.add_argument("--change-type", default="greenfield", choices=["greenfield", "brownfield", "external", "bugfix"])
    parser.add_argument("--demo", action="store_true", help="Run self-check")
    args = parser.parse_args()

    if args.demo:
        return demo()

    if not args.candidate:
        parser.error("--candidate required (or use --demo)")

    thresholds = {
        "max_error_rate": args.max_error_rate,
        "max_avg_latency_ms": args.max_avg_latency_ms,
        "max_max_latency_ms": args.max_max_latency_ms,
    }

    results = run_pipeline(
        candidate_traces=args.candidate,
        baseline_traces=args.baseline,
        corpus=args.corpus,
        thresholds=thresholds,
        gates=args.gates,
        specs_dir=args.specs_dir,
        change_type=args.change_type,
    )

    report = render_report(results)
    print(report)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report + "\n")

    return 0 if results["overall"] == "approved" else 1


if __name__ == "__main__":
    sys.exit(main())
