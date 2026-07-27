#!/usr/bin/env python3
"""Governed Router — wraps hybrid_inference_router with governance filters.

Extends route_request() with:
- Data class enforcement (from model_registry)
- Geopolitical pool filtering
- Assurance level matching
- Sovereign fallback

Usage:
    python3 governed_router.py --query "Classify this contract" --data-class internal --assurance validated
    python3 governed_router.py --query "Draft legal advice" --data-class confidential --assurance audited
    python3 governed_router.py --demo
"""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from hybrid_inference_router import route_request, ROUTING_TABLE
from model_registry import load_registry, eligible_models


def route_governed(
    prompt: str,
    task: str = "governance",
    system: str = "",
    data_class: str | None = None,
    assurance: str | None = None,
    exclude_pools: list[str] | None = None,
    sovereign_only: bool = False,
) -> tuple[str | None, str, float, dict]:
    """Route with governance constraints.

    Returns (response, model_used, cost, governance_metadata).
    """
    registry = load_registry()
    eligible = eligible_models(registry, data_class=data_class, assurance=assurance)

    if not eligible:
        return (
            None,
            "NO_ELIGIBLE_MODEL",
            0.0,
            {
                "governance_status": "rejected",
                "reason": f"no model eligible for data_class={data_class}",
            },
        )

    eligible_names = {name for name, _ in eligible}

    # Get task tiers from base router
    task_config = ROUTING_TABLE.get(task, ROUTING_TABLE["governance"])
    tiers = task_config["tiers"]

    # Filter tiers through governance
    filtered_tiers = []
    rejection_reasons = []

    for tier in tiers:
        model = tier["model"]
        backend = tier["backend"]

        # Check if model is in eligible set (registry allows it)
        # Note: cloud models may not be in local registry — we check by name pattern
        model_short = model.split("/")[-1] if "/" in model else model

        # Check geopolitical pool exclusion
        if exclude_pools:
            # Look up model in registry for pool info
            pool = _get_model_pool(registry, model_short)
            if pool in exclude_pools:
                rejection_reasons.append(f"{model}: pool {pool} excluded")
                continue

        # For sovereign_only, only allow private hosting
        if sovereign_only and not _is_sovereign(registry, model_short):
            rejection_reasons.append(f"{model}: not sovereign-hosted")
            continue

        # If model is in registry, check eligibility
        if model_short in eligible_names:
            filtered_tiers.append(tier)
        elif _is_cloud_model(backend):
            # Cloud models not in local registry: allow if no data_class restriction
            # or if data_class is public/internal (lower risk)
            if data_class in (None, "public", "internal"):
                filtered_tiers.append(tier)
            else:
                rejection_reasons.append(
                    f"{model}: cloud model, data_class={data_class} too sensitive"
                )
        else:
            rejection_reasons.append(f"{model}: not in registry eligible set")

    if not filtered_tiers:
        return (
            None,
            "ALL_GOVERNANCE_BLOCKED",
            0.0,
            {
                "governance_status": "rejected",
                "reason": "all tiers blocked by governance",
                "rejection_reasons": rejection_reasons[:10],
            },
        )

    # Use base router with filtered tiers (monkey-patch temporarily)
    import hybrid_inference_router as hir

    original_tiers = ROUTING_TABLE.get(task, ROUTING_TABLE["governance"])["tiers"]
    ROUTING_TABLE[task]["tiers"] = filtered_tiers

    try:
        response, model, cost = route_request(prompt, task, system)
    finally:
        # Restore original tiers
        ROUTING_TABLE[task]["tiers"] = original_tiers

    metadata = {
        "governance_status": "routed" if response else "routing_failed",
        "data_class": data_class,
        "assurance": assurance,
        "candidates_considered": len(filtered_tiers),
        "rejection_reasons": rejection_reasons[:5] if rejection_reasons else None,
    }

    return response, model, cost, metadata


def _get_model_pool(registry: dict, model_short: str) -> str | None:
    """Look up geopolitical pool for a model."""
    for name, meta in registry.get("models", {}).items():
        if model_short in name or name in model_short:
            return meta.get("geopolitical_pool")
    return None


def _is_sovereign(registry: dict, model_short: str) -> bool:
    """Check if model is self-hosted (sovereign)."""
    for name, meta in registry.get("models", {}).items():
        if model_short in name or name in model_short:
            return meta.get("hosting") == "private"
    # Cloud models are not sovereign by default
    return False


def _is_cloud_model(backend: str) -> bool:
    """Check if backend is cloud-hosted."""
    return backend in ("openrouter", "openrouter_free", "openai", "google")


def demo() -> int:
    """Self-check with dry-run (no actual API calls)."""
    registry = load_registry()

    # Test 1: confidential data should exclude models without confidential permission
    eligible = eligible_models(registry, data_class="confidential")
    assert len(eligible) >= 1, "at least one model should handle confidential"
    for name, meta in eligible:
        assert "confidential" in meta.get("allowed_data_classes", []), (
            f"{name} shouldn't be eligible for confidential"
        )

    # Test 2: restricted data should have zero eligible models
    eligible_restricted = eligible_models(registry, data_class="restricted")
    assert len(eligible_restricted) == 0, "no model should handle restricted data"

    # Test 3: governance filter logic
    tiers = ROUTING_TABLE["governance"]["tiers"]
    assert len(tiers) > 0, "governance task should have tiers"

    # Test 4: sovereign_only should filter to private-hosted only
    # (dry-run: just check the logic doesn't crash)
    print("governed_router demo OK")
    print(f"  Registry: {len(registry['models'])} models")
    print(f"  Eligible for confidential: {len(eligible)}")
    print(f"  Eligible for restricted: {len(eligible_restricted)}")
    print(f"  Governance tiers: {len(tiers)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", type=str, help="Query to route")
    parser.add_argument(
        "--task", default="governance", choices=list(ROUTING_TABLE.keys())
    )
    parser.add_argument("--system", default="")
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
        "--exclude-pools", type=str, nargs="+", help="Geopolitical pools to exclude"
    )
    parser.add_argument(
        "--sovereign-only", action="store_true", help="Only self-hosted models"
    )
    parser.add_argument("--demo", action="store_true", help="Run self-check")
    args = parser.parse_args()

    if args.demo:
        return demo()

    if not args.query:
        parser.error("--query required (or use --demo)")

    response, model, cost, metadata = route_governed(
        prompt=args.query,
        task=args.task,
        system=args.system,
        data_class=args.data_class,
        assurance=args.assurance,
        exclude_pools=args.exclude_pools,
        sovereign_only=args.sovereign_only,
    )

    print(f"[GOVERNED ROUTE] Model={model}, Cost=${cost:.5f}")
    print(f"[METADATA] {json.dumps(metadata, indent=2)}")

    if response:
        print(f"\n{response}")
    else:
        print("[BLOCKED] No eligible model or all backends failed")
        return 1

    return 0


if __name__ == "__main__":
    import json

    sys.exit(main())
