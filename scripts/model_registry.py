#!/usr/bin/env python3
"""Model Capability Registry — single source of truth for model metadata.

Extends existing hybrid_inference_router.py ROUTING_TABLE with governance metadata:
- License, hosting, data class permissions
- Benchmark results, known failure modes
- Security status, lifecycle state
- Geopolitical risk level

Usage:
    python3 scripts/model_registry.py --list
    python3 scripts/model_registry.py --model qwen2.5:14b-instruct-q4_K_M
    python3 scripts/model_registry.py --validate models.yaml
    python3 scripts/model_registry.py --eligible --data-class internal --assurance validated
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).parent.parent
REGISTRY_PATH = REPO_ROOT / "models" / "registry.json"
POLICIES_PATH = REPO_ROOT / "policies" / "model-lifecycle.yaml"

# Built-in registry — extends ROUTING_TABLE from hybrid_inference_router.py
# with governance metadata that the router doesn't track.
DEFAULT_REGISTRY = {
    "models": {
        "qwen2.5:14b-instruct-q4_K_M": {
            "provider": "ollama",
            "hosting": "private",
            "license": "apache-2.0",
            "context_window": 32768,
            "geopolitical_pool": "tier_2_verified",
            "benchmarks": {"apex_r9_overall": 0.72, "apex_r9_legal_reasoning": 0.68},
            "allowed_data_classes": ["public", "internal", "confidential"],
            "forbidden_data_classes": ["restricted"],
            "cost_per_1m_tokens": 0.0,
            "latency_p95_ms": 4500,
            "known_failure_modes": ["hallucinated_citations", "language_mixing"],
            "security_status": "scanned",
            "lifecycle_state": "production",
            "last_evaluated": "2026-07-23",
            "eval_version": "apex-r9",
        },
        "qwen2.5-coder:7b": {
            "provider": "ollama",
            "hosting": "private",
            "license": "apache-2.0",
            "context_window": 32768,
            "geopolitical_pool": "tier_2_verified",
            "benchmarks": {"apex_r9_overall": 0.61, "apex_r9_code_generation": 0.74},
            "allowed_data_classes": ["public", "internal"],
            "forbidden_data_classes": ["confidential", "restricted"],
            "cost_per_1m_tokens": 0.0,
            "latency_p95_ms": 2200,
            "known_failure_modes": ["incomplete_responses"],
            "security_status": "scanned",
            "lifecycle_state": "production",
            "last_evaluated": "2026-07-23",
            "eval_version": "apex-r9",
        },
        "llama3.1:8b": {
            "provider": "ollama",
            "hosting": "private",
            "license": "llama3.1",
            "context_window": 8192,
            "geopolitical_pool": "tier_1_trusted",
            "benchmarks": {"apex_r9_overall": 0.58, "apex_r9_legal_reasoning": 0.55},
            "allowed_data_classes": ["public", "internal"],
            "forbidden_data_classes": ["confidential", "restricted"],
            "cost_per_1m_tokens": 0.0,
            "latency_p95_ms": 1800,
            "known_failure_modes": ["citation_hallucination", "over_refusal"],
            "security_status": "scanned",
            "lifecycle_state": "production",
            "last_evaluated": "2026-07-23",
            "eval_version": "apex-r9",
        },
        "qwen2.5:32b-instruct-q4_K_M": {
            "provider": "ollama",
            "hosting": "private",
            "license": "apache-2.0",
            "context_window": 32768,
            "geopolitical_pool": "tier_2_verified",
            "benchmarks": {"apex_r9_overall": 0.82, "apex_r9_judge_quality": 0.79},
            "allowed_data_classes": ["public", "internal", "confidential"],
            "forbidden_data_classes": ["restricted"],
            "cost_per_1m_tokens": 0.0,
            "latency_p95_ms": 8000,
            "known_failure_modes": ["slow_on_short_tasks"],
            "security_status": "scanned",
            "lifecycle_state": "production",
            "last_evaluated": "2026-07-23",
            "eval_version": "apex-r9",
        },
    }
}


def load_registry(path: Path | None = None) -> dict:
    """Load registry from JSON or return default."""
    path = path or REGISTRY_PATH
    if not path.exists():
        return DEFAULT_REGISTRY
    return json.loads(path.read_text())


def list_models(registry: dict) -> str:
    """Format registry as markdown table."""
    lines = ["# Model Capability Registry", ""]
    lines.append("| model | hosting | license | state | overall | data classes |")
    lines.append("|-------|---------|---------|-------|---------|--------------|")
    for name, meta in sorted(registry["models"].items()):
        benchmarks = meta.get("benchmarks", {})
        overall = benchmarks.get("apex_r9_overall", "?")
        data_classes = ", ".join(meta.get("allowed_data_classes", []))
        lines.append(
            f"| {name} | {meta.get('hosting', '?')} | {meta.get('license', '?')} "
            f"| {meta.get('lifecycle_state', '?')} | {overall} | {data_classes} |"
        )
    return "\n".join(lines)


def get_model(registry: dict, model_id: str) -> dict | None:
    """Get single model metadata."""
    return registry.get("models", {}).get(model_id)


def eligible_models(
    registry: dict,
    data_class: str | None = None,
    assurance: str | None = None,
    tier: str | None = None,
) -> list[tuple[str, dict]]:
    """Filter models by governance constraints."""
    results = []
    for name, meta in registry.get("models", {}).items():
        if meta.get("lifecycle_state") != "production":
            continue
        if data_class and data_class not in meta.get("allowed_data_classes", []):
            continue
        if meta.get("security_status") != "scanned":
            continue
        results.append((name, meta))
    return results


def validate_registry(registry: dict) -> list[str]:
    """Validate registry completeness. Returns list of errors."""
    errors = []
    required_fields = [
        "provider",
        "hosting",
        "license",
        "context_window",
        "allowed_data_classes",
        "security_status",
        "lifecycle_state",
    ]
    for name, meta in registry.get("models", {}).items():
        for field in required_fields:
            if field not in meta:
                errors.append(f"{name}: missing required field '{field}'")
        # Check lifecycle state validity
        valid_states = [
            "quarantined",
            "evaluated",
            "validated",
            "staged",
            "production",
            "deprecated",
        ]
        if meta.get("lifecycle_state") not in valid_states:
            errors.append(
                f"{name}: invalid lifecycle_state '{meta.get('lifecycle_state')}'"
            )
        # Check data class validity
        valid_classes = ["public", "internal", "confidential", "restricted"]
        for dc in meta.get("allowed_data_classes", []):
            if dc not in valid_classes:
                errors.append(f"{name}: invalid data_class '{dc}'")
    return errors


def demo() -> int:
    """Self-check."""
    reg = load_registry()
    assert len(reg["models"]) >= 4

    # Test eligibility filter
    eligible = eligible_models(reg, data_class="confidential")
    assert len(eligible) >= 1, "at least one model should handle confidential"

    # Test validation
    errors = validate_registry(reg)
    assert not errors, f"validation errors: {errors}"

    # Test single model lookup
    model = get_model(reg, "qwen2.5:14b-instruct-q4_K_M")
    assert model is not None
    assert model["lifecycle_state"] == "production"

    print("model_registry demo OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="List all models")
    parser.add_argument("--model", type=str, help="Show single model details")
    parser.add_argument("--eligible", action="store_true", help="List eligible models")
    parser.add_argument(
        "--data-class",
        type=str,
        choices=["public", "internal", "confidential", "restricted"],
    )
    parser.add_argument(
        "--assurance",
        type=str,
        choices=["best_effort", "validated", "audited", "certified"],
    )
    parser.add_argument(
        "--tier", type=str, choices=["commodity", "differentiated", "frontier"]
    )
    parser.add_argument("--validate", action="store_true", help="Validate registry")
    parser.add_argument("--demo", action="store_true", help="Run self-check")
    args = parser.parse_args()

    if args.demo:
        return demo()

    registry = load_registry()

    if args.validate:
        errors = validate_registry(registry)
        if errors:
            for e in errors:
                print(f"ERROR: {e}")
            return 1
        print("registry valid")
        return 0

    if args.list:
        print(list_models(registry))
        return 0

    if args.model:
        model = get_model(registry, args.model)
        if not model:
            print(f"model '{args.model}' not found", file=sys.stderr)
            return 1
        print(json.dumps(model, indent=2))
        return 0

    if args.eligible:
        results = eligible_models(registry, args.data_class, args.assurance, args.tier)
        for name, meta in results:
            print(
                f"{name}: state={meta['lifecycle_state']} classes={meta.get('allowed_data_classes', [])}"
            )
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
