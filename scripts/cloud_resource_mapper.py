#!/usr/bin/env python3
"""Map all available cloud resources and find optimal model routing.

Analyzes all available API keys, subscriptions, and model capabilities
to produce an optimal resource allocation plan for OpenDjicht-1.

Usage:
  python3 scripts/cloud_resource_mapper.py
  python3 scripts/cloud_resource_mapper.py --test-apis
  python3 scripts/cloud_resource_mapper.py --output cloud_resources.json
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
OUTPUT_PATH = REPO_ROOT / "analysis" / "openmythos-apex-runs" / "cloud_resources.json"

# All available API endpoints
ENDPOINTS = {
    "openai_direct": {
        "url": "https://api.openai.com/v1/chat/completions",
        "env_key": "OPENAI_API_KEY",
        "models": ["gpt-5", "gpt-5-mini", "gpt-4o", "gpt-4o-mini"],
        "type": "frontier_teacher",
        "cost_per_1m_prompt": 2.50,
        "cost_per_1m_completion": 10.00,
        "context": 128000,
    },
    "opencode_openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "env_key": "OPENCODE_OPENAI_API_KEY",
        "models": ["gpt-5", "gpt-5-mini", "gpt-4o", "gpt-4o-mini"],
        "type": "frontier_teacher",
        "cost_per_1m_prompt": 2.50,
        "cost_per_1m_completion": 10.00,
        "context": 128000,
    },
    "anthropic": {
        "url": "https://api.anthropic.com/v1/messages",
        "env_key": "ANTHROPIC_API_KEY",
        "models": ["claude-opus-4.8", "claude-sonnet-4.6", "claude-sonnet-4"],
        "type": "frontier_teacher",
        "cost_per_1m_prompt": 3.00,
        "cost_per_1m_completion": 15.00,
        "context": 1000000,
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "env_key": "OPENROUTER_API_KEY",
        "models": [
            "anthropic/claude-opus-4.8",
            "anthropic/claude-sonnet-4.6",
            "openai/gpt-5",
            "openai/gpt-5.4",
            "google/gemini-2.5-pro",
            "google/gemini-3.5-flash",
            "google/gemini-3.6-flash",
            "deepseek/deepseek-v4-pro",
            "moonshotai/kimi-k2.7-code",
            "moonshotai/kimi-k2.6",
            "qwen/qwen3.5-397b",
            "qwen/qwen3-coder-480b",
        ],
        "type": "frontier_teacher",
        "cost_per_1m_prompt": 0.00001,
        "cost_per_1m_completion": 0.00003,
        "context": 1000000,
    },
    "openrouter_free": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "env_key": "OPENROUTER_API_KEY",
        "models": [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b:free",
            "qwen/qwen3.5-flash-02-23",
            "qwen/qwen3-235b-a22b-2507",
            "qwen/qwen3-next-80b-a3b-thinking",
            "deepseek/deepseek-v4-flash",
            "google/gemini-3-flash-preview",
            "google/gemini-2.5-flash-lite",
            "moonshotai/kimi-k2-thinking",
            "z-ai/glm-4.7-flash",
            "nvidia/nemotron-3-super-120b-a12b:free",
        ],
        "type": "free_teacher",
        "cost_per_1m_prompt": 0,
        "cost_per_1m_completion": 0,
        "context": 1000000,
    },
    "ollama_cloud": {
        "url": "https://ollama.com/api",
        "env_key": "OLLAMA_API_KEY",
        "models": [
            "qwen3.5:397b",
            "qwen3-coder:480b",
            "kimi-k2:1t",
            "kimi-k2-thinking",
            "kimi-k2.6",
            "deepseek-v4-flash",
            "deepseek-v4-pro",
            "glm-5.1",
            "gemma4:31b",
            "nemotron-3-super",
            "gemini-3-flash-preview",
        ],
        "type": "ollama_cloud",
        "cost_per_1m_prompt": 0,
        "cost_per_1m_completion": 0,
        "context": 131072,
    },
    "google_gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta",
        "env_key": "GEMINI_API_KEY",
        "models": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-3-flash"],
        "type": "frontier_teacher",
        "cost_per_1m_prompt": 1.25,
        "cost_per_1m_completion": 10.00,
        "context": 1048576,
    },
    "requesty": {
        "url": os.environ.get("REQUESTY_BASE_URL", ""),
        "env_key": "REQUESTY_API_KEY",
        "models": ["gpt-5", "deepseek-pro", "gemini-flash"],
        "type": "proxy_teacher",
        "cost_per_1m_prompt": 0.50,
        "cost_per_1m_completion": 2.00,
        "context": 128000,
    },
}

# Optimal routing for OpenDjicht-1 data generation
OPTIMAL_ROUTING = {
    "governance_expert_teacher": {
        "primary": ("openrouter", "anthropic/claude-opus-4.8"),
        "fallback": ("anthropic", "claude-opus-4.8"),
        "rationale": "Beste governance reasoning, 1M context",
    },
    "bulk_data_generation": {
        "primary": ("openrouter_free", "qwen/qwen3.5-flash-02-23"),
        "fallback": ("openrouter_free", "deepseek/deepseek-v4-flash"),
        "rationale": "Gratis, 1M context, goed genoeg voor SFT data",
    },
    "dpo_chosen_generation": {
        "primary": ("openrouter", "openai/gpt-5.4"),
        "fallback": ("openrouter", "anthropic/claude-sonnet-4.6"),
        "rationale": "Frontier quality voor DPO chosen responses",
    },
    "dpo_rejected_generation": {
        "primary": ("openrouter_free", "openai/gpt-oss-120b"),
        "fallback": ("ollama_cloud", "qwen3.5:397b"),
        "rationale": "Goed maar niet perfect = ideaal als rejected",
    },
    "nl_governance_teacher": {
        "primary": ("openrouter", "google/gemini-2.5-pro"),
        "fallback": ("google_gemini", "gemini-2.5-pro"),
        "rationale": "Sterk in meertaligheid, EU context",
    },
    "code_governance_teacher": {
        "primary": ("openrouter", "moonshotai/kimi-k2.7-code"),
        "fallback": ("openrouter_free", "qwen/qwen3-coder-480b"),
        "rationale": "Tool-scope en code governance specialist",
    },
    "reasoning_governance_teacher": {
        "primary": ("openrouter_free", "qwen/qwen3-next-80b-a3b-thinking"),
        "fallback": ("openrouter", "openai/gpt-5.4"),
        "rationale": "Complex reasoning voor calibration en value-alignment",
    },
    "fast_judge": {
        "primary": ("openrouter_free", "google/gemini-2.5-flash-lite"),
        "fallback": ("openrouter_free", "deepseek/deepseek-v4-flash"),
        "rationale": "Gratis, snel, goed voor LLM-as-judge",
    },
}


def check_api_available(endpoint_name: str, config: dict) -> dict:
    """Check if an API endpoint is available."""
    env_key = config.get("env_key", "")
    api_key = os.environ.get(env_key, "")

    if not api_key:
        return {"available": False, "reason": f"No {env_key} in env"}

    # Simple reachability check
    url = config.get("url", "")
    if not url:
        return {"available": False, "reason": "No URL"}

    try:
        req = urllib.request.Request(
            url.replace("/chat/completions", "/models").replace(
                "/v1/messages", "/v1/models"
            ),
            headers={"Authorization": f"Bearer {api_key}"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return {"available": True, "status": resp.status}
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return {"available": False, "reason": "Invalid API key"}
        return {"available": True, "status": e.code}  # 404 etc means reachable
    except Exception:
        return {"available": False, "reason": "Unreachable"}


def generate_plan() -> dict:
    """Generate the complete resource plan."""
    plan = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "apis": {},
        "optimal_routing": OPTIMAL_ROUTING,
        "cost_optimization": {},
        "recommended_workflow": {},
    }

    # Check each API
    for name, config in ENDPOINTS.items():
        result = check_api_available(name, config)
        plan["apis"][name] = {
            "available": result["available"],
            "reason": result.get("reason", ""),
            "models": config.get("models", []),
            "type": config.get("type", ""),
            "cost_per_1m_prompt": config.get("cost_per_1m_prompt", 0),
            "cost_per_1m_completion": config.get("cost_per_1m_completion", 0),
            "context": config.get("context", 0),
        }

    # Cost optimization analysis
    available_apis = [n for n, v in plan["apis"].items() if v["available"]]
    free_apis = [
        n for n in available_apis if plan["apis"][n].get("cost_per_1m_prompt", 0) == 0
    ]

    plan["cost_optimization"] = {
        "available_apis": available_apis,
        "free_apis": free_apis,
        "estimated_cost_per_1000_cases": {
            "all_paid": "~${:.2f}".format(1000 * 2 * 0.005),  # ~$10
            "optimal_mix": "~${:.2f}".format(1000 * 2 * 0.001),  # ~$2
            "all_free": "$0.00",
        },
        "recommendation": "Use OpenRouter free models for 80% of generation, paid frontier for 20% high-value DPO chosen",
    }

    # Recommended workflow
    plan["recommended_workflow"] = {
        "step_1_generate_sft": {
            "description": "Generate SFT training data from free frontier models",
            "endpoint": "openrouter_free",
            "model": "qwen/qwen3.5-flash-02-23",
            "cases": 200,
            "estimated_cost": "$0",
        },
        "step_2_generate_dpo_chosen": {
            "description": "Generate frontier-quality chosen responses",
            "endpoint": "openrouter",
            "model": "anthropic/claude-opus-4.8",
            "cases": 100,
            "estimated_cost": "$0.50",
        },
        "step_3_generate_dpo_rejected": {
            "description": "Generate good-but-imperfect rejected responses",
            "endpoint": "openrouter_free",
            "model": "openai/gpt-oss-120b",
            "cases": 100,
            "estimated_cost": "$0",
        },
        "step_4_nl_governance": {
            "description": "Generate Dutch governance cases",
            "endpoint": "openrouter",
            "model": "google/gemini-2.5-pro",
            "cases": 50,
            "estimated_cost": "$0.25",
        },
        "step_5_upload_train": {
            "description": "Upload to OpenAI fine-tuning + train",
            "endpoint": "openai_direct",
            "model": "gpt-4o-mini",
            "estimated_cost": "$10-30",
        },
        "total_estimated_cost": "$11-31",
    }

    return plan


def main() -> int:
    print("=" * 60)
    print("  OpenDjicht-1 Cloud Resource Mapper")
    print("=" * 60)

    plan = generate_plan()

    print("\n=== Available APIs ===")
    for name, info in plan["apis"].items():
        status = "✅" if info["available"] else "❌"
        cost = (
            f"${info['cost_per_1m_completion']:.5f}/1M completion"
            if info["cost_per_1m_completion"] > 0
            else "FREE"
        )
        print(f"  {status} {name:25s} {info['type']:20s} {cost}")
        if not info["available"] and info.get("reason"):
            print(f"     → {info['reason']}")
        for m in info.get("models", [])[:3]:
            print(f"       - {m}")

    print("\n=== Cost Optimization ===")
    opt = plan["cost_optimization"]
    print(f"  Available APIs: {len(opt['available_apis'])}")
    print(f"  Free APIs: {len(opt['free_apis'])}")
    print(f"  Cost per 1000 cases:")
    for tier, cost in opt["estimated_cost_per_1000_cases"].items():
        print(f"    {tier}: {cost}")
    print(f"  → {opt['recommendation']}")

    print("\n=== Recommended Workflow ===")
    total_cost = "$0"
    for step, info in plan["recommended_workflow"].items():
        if isinstance(info, dict) and "model" in info:
            print(f"  {step}:")
            print(f"    {info['description']}")
            print(f"    Model: {info['model']}")
            print(f"    Cases: {info.get('cases', 'N/A')}")
            print(f"    Cost: {info.get('estimated_cost', 'N/A')}")

    # Save plan
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(plan, indent=2, sort_keys=True))
    print(f"\n[Saved] {OUTPUT_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
