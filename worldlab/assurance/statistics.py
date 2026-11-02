"""Small dependency-free descriptive statistics for replicated experiments."""

from __future__ import annotations

import math
import statistics


def summarize(values: list[float]) -> dict:
    if not values:
        return {"n": 0, "mean": None, "median": None, "variance": None, "confidence_interval_95": [None, None]}
    mean = statistics.fmean(values)
    variance = statistics.variance(values) if len(values) > 1 else 0.0
    margin = 1.96 * math.sqrt(variance / len(values)) if len(values) > 1 else 0.0
    return {"n": len(values), "mean": mean, "median": statistics.median(values), "variance": variance,
            "confidence_interval_95": [mean - margin, mean + margin]}


def compare(control: list[float], treatment: list[float], minimum_effect: float = 0.0) -> dict:
    left, right = summarize(control), summarize(treatment)
    effect = (left["mean"] or 0.0) - (right["mean"] or 0.0)
    # Conservative interval for the difference of independent means.
    standard_error = math.sqrt((left["variance"] or 0.0) / max(1, left["n"]) + (right["variance"] or 0.0) / max(1, right["n"]))
    interval = [effect - 1.96 * standard_error, effect + 1.96 * standard_error]
    return {"control": left, "treatment": right, "effect": effect, "confidence_interval_95": interval,
            "operationally_meaningful": interval[0] > minimum_effect}


def compare_paired(control: list[float], treatment: list[float], minimum_effect: float = 0.0) -> dict:
    if len(control) != len(treatment) or not control:
        raise ValueError("paired comparison requires equal non-empty samples")
    left, right = summarize(control), summarize(treatment)
    differences = summarize([a - b for a, b in zip(control, treatment)])
    return {"control": left, "treatment": right, "effect": differences["mean"],
            "confidence_interval_95": differences["confidence_interval_95"],
            "operationally_meaningful": differences["confidence_interval_95"][0] > minimum_effect,
            "paired": True}
