"""Diagnostic reviewer-independence vector; intentionally no weighted score."""

DIMENSIONS = ("model_family", "provider", "prompt", "context", "memory", "retrieval", "oracle")


def assess(maker: dict, checker: dict) -> dict:
    vector = {}
    for dimension in DIMENSIONS:
        left, right = maker.get(dimension), checker.get(dimension)
        vector[f"{dimension}_independence"] = "UNDETERMINED" if left is None or right is None else "PASS" if left != right else "FAIL"
    failures = [key for key, value in vector.items() if value == "FAIL"]
    return {"vector": vector, "correlated_failure_risk": "HIGH" if failures else "UNDETERMINED" if "UNDETERMINED" in vector.values() else "LOW",
            "failed_dimensions": failures}
