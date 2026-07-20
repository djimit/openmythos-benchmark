#!/usr/bin/env python3
"""McNemar's test for paired binary outcomes in A/B testing.

Replaces the deterministic rule in r23_adapter_ab.py with a proper
statistical test for paired nominal data.

Usage:
    python3 mcnemar_test.py --before before.jsonl --after after.jsonl
"""
import argparse
import json
import sys
from math import comb
from pathlib import Path


def mcnemar_test(before: list[bool], after: list[bool], exact: bool = True) -> dict:
    """McNemar's test for paired binary outcomes.

    Args:
        before: list of pass/fail for model A (baseline)
        after: list of pass/fail for model B (candidate)
        exact: use exact binomial test (recommended for n < 25)

    Returns:
        dict with statistic, p_value, and interpretation
    """
    if len(before) != len(after):
        raise ValueError(f"Length mismatch: {len(before)} vs {len(after)}")

    # Contingency table:
    #   b00: both fail  |  b01: before fail, after pass
    #   b10: before pass, after fail  |  b11: both pass
    b00 = sum(1 for b, a in zip(before, after) if not b and not a)
    b01 = sum(1 for b, a in zip(before, after) if not b and a)
    b10 = sum(1 for b, a in zip(before, after) if b and not a)
    b11 = sum(1 for b, a in zip(before, after) if b and a)

    n_discordant = b01 + b10
    if n_discordant == 0:
        return {"statistic": 0, "p_value": 1.0, "interpretation": "No discordant pairs — no evidence of difference",
                "table": {"b00": b00, "b01": b01, "b10": b10, "b11": b11}}

    if exact:
        # Exact binomial test: under H0, b01 ~ Binomial(n_discordant, 0.5)
        p_value = 2 * sum(comb(n_discordant, k) * 0.5**n_discordant for k in range(min(b01, b10) + 1))
        p_value = min(p_value, 1.0)
    else:
        # Chi-squared approximation (with continuity correction)
        chi2 = (abs(b01 - b10) - 1)**2 / n_discordant if n_discordant > 0 else 0
        from math import erfc, sqrt
        p_value = erfc(sqrt(chi2 / 2))

    alpha = 0.05
    if p_value < alpha:
        if b01 > b10:
            interpretation = f"Significant improvement (p={p_value:.4f}): {b01} improved vs {b10} regressed"
        else:
            interpretation = f"Significant regression (p={p_value:.4f}): {b10} regressed vs {b01} improved"
    else:
        interpretation = f"No significant difference (p={p_value:.4f})"

    return {"statistic": abs(b01 - b10), "p_value": round(p_value, 6), "interpretation": interpretation,
            "table": {"b00": b00, "b01": b01, "b10": b10, "b11": b11}}


def main():
    parser = argparse.ArgumentParser(description="McNemar's test for A/B binary outcomes")
    parser.add_argument("--before", required=True, help="JSONL with baseline results (field: passed)")
    parser.add_argument("--after", required=True, help="JSONL with candidate results (field: passed)")
    parser.add_argument("--exact", action="store_true", default=True, help="Use exact binomial test")
    args = parser.parse_args()

    before_data = [json.loads(l) for l in Path(args.before).read_text().splitlines() if l.strip()]
    after_data = [json.loads(l) for l in Path(args.after).read_text().splitlines() if l.strip()]

    before_passed = [d.get("passed", d.get("pass", False)) for d in before_data]
    after_passed = [d.get("passed", d.get("pass", False)) for d in after_data]

    result = mcnemar_test(before_passed, after_passed, args.exact)
    print(json.dumps(result, indent=2))
    return 0 if result["p_value"] >= 0.05 or result["table"]["b01"] > result["table"]["b10"] else 1


if __name__ == "__main__":
    sys.exit(main())
