"""Explicitly enabled local Ollama transport for post-core research campaigns."""

from __future__ import annotations

import json
import os
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from worldlab.runtime.agent_adapter import WorldAgentAdapter


def ollama_adapter(agent_id: str, model: str, base_url: str = "http://127.0.0.1:11434") -> WorldAgentAdapter:
    if os.getenv("WORLDLAB_EXTERNAL_MODELS_ENABLED") != "1":
        raise RuntimeError("WORLDLAB_EXTERNAL_MODELS_DISABLED")
    host = urlparse(base_url).hostname
    if host not in {"127.0.0.1", "localhost", "::1"} and os.getenv("WORLDLAB_REMOTE_MODELS_ENABLED") != "1":
        raise RuntimeError("WORLDLAB_REMOTE_MODEL_FORBIDDEN")

    def generate(context: dict) -> dict:
        prompt = str(context.get("prompt", ""))
        body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                           **({"format": "json"} if context.get("json") else {}),
                           "options": {"temperature": float(context.get("temperature", 0)), "seed": int(context.get("seed", 0)),
                                       "num_predict": int(context.get("max_tokens", 80))}}).encode()
        request = Request(f"{base_url.rstrip('/')}/api/generate", data=body, headers={"content-type": "application/json"})
        with urlopen(request, timeout=float(context.get("timeout", 120))) as response:
            payload = json.loads(response.read())
        return {"text": payload.get("response", ""), "tokens": payload.get("eval_count"), "cost": None}

    return WorldAgentAdapter(agent_id, generate, provider="ollama", model=model, version="local")


def ollama_model_metadata(models: list[str], base_url: str = "http://127.0.0.1:11434") -> list[dict]:
    if os.getenv("WORLDLAB_EXTERNAL_MODELS_ENABLED") != "1":
        raise RuntimeError("WORLDLAB_EXTERNAL_MODELS_DISABLED")
    with urlopen(f"{base_url.rstrip('/')}/api/tags", timeout=10) as response:
        available = {item["name"]: item for item in json.loads(response.read()).get("models", [])}
    return [{"name": model, "digest": available.get(model, {}).get("digest"),
             "size": available.get(model, {}).get("size"), "modified_at": available.get(model, {}).get("modified_at")}
            for model in models]
