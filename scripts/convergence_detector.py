#!/usr/bin/env python3
"""Convergence detection for the OpenMythos evolution loop.

Tracks corpus quality metrics across evolution steps and determines
when the loop has plateaued (no further improvement expected).

Usage:
    python3 convergence_detector.py --history metrics.jsonl --window 3 --threshold 0.02
"""
import argparse
import json
import sys
from pathlib import Path


def detect_convergence(history: list[dict], window: int = 3, threshold: float = 0.02) -> dict:
    """Detect if the evolution loop has converged.

    Args:
        history: list of {step, dead_rate, avg_spread, avg_score} dicts
        window: number of recent steps to consider
        threshold: if metric change < threshold for window steps, converged

    Returns:
        dict with converged bool and diagnostics
    """
    if len(history) < window + 1:
        return {"converged": False, "reason": f"Need {window+1} steps, have {len(history)}"}

    recent = history[-window:]
    metrics = ["dead_rate", "avg_spread", "avg_score"]
    converged_metrics = []

    for metric in metrics:
        values = [h.get(metric, 0) for h in recent]
        if len(values) < 2:
            continue
        max_change = max(abs(values[i] - values[i-1]) for i in range(1, len(values)))
        if max_change < threshold:
            converged_metrics.append(metric)

    all_converged = len(converged_metrics) == len(metrics)
    return {
        "converged": all_converged,
        "converged_metrics": converged_metrics,
        "pending_metrics": [m for m in metrics if m not in converged_metrics],
        "recent_values": {m: [h.get(m) for h in recent] for m in metrics},
        "recommendation": "STOP" if all_converged else "CONTINUE",
    }


def main():
    parser = argparse.ArgumentParser(description="Detect evolution convergence")
    parser.add_argument("--history", required=True, help="JSONL with step metrics")
    parser.add_argument("--window", type=int, default=3, help="Steps to evaluate")
    parser.add_argument("--threshold", type=float, default=0.02, help="Convergence threshold")
    args = parser.parse_args()

    history = [json.loads(l) for l in Path(args.history).read_text().splitlines() if l.strip()]
    result = detect_convergence(history, args.window, args.threshold)
    print(json.dumps(result, indent=2))
    return 0 if result["converged"] else 1


if __name__ == "__main__":
    sys.exit(main())
