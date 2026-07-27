#!/usr/bin/env python3
"""Run benchmark cases against a model via Ollama or OpenAI-compatible API."""

import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CORPUS_PATH = REPO_ROOT / "cases" / "corpus.jsonl"


def load_corpus(path: Path = CORPUS_PATH) -> list[dict]:
    cases = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def call_ollama(
    prompt: str,
    model: str,
    base_url: str = "http://localhost:11434",
    num_predict: int | None = None,
    timeout: int = 120,
    system: str | None = None,
) -> dict:
    """Call Ollama API."""
    import urllib.request

    url = f"{base_url}/api/generate"
    body = {"model": model, "prompt": prompt, "stream": False}
    if num_predict:
        body["options"] = {"num_predict": num_predict}
    if system:
        body["system"] = system
    payload = json.dumps(body).encode()
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    start = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        result = json.loads(resp.read())
    elapsed = time.time() - start
    return {
        "response": result.get("response", ""),
        "tokens": result.get("eval_count", 0),
        "latency_ms": round(elapsed * 1000, 1),
    }


def call_openai_chat(
    prompt: str, model: str, api_key: str = None, base_url: str = None
) -> dict:
    """Call OpenAI-compatible API."""
    import urllib.request

    api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
    base_url = base_url or os.environ.get(
        "OPENAI_BASE_URL", "https://api.openai.com/v1"
    )
    url = f"{base_url}/chat/completions"
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 512,
            "temperature": 0,
        }
    ).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    start = time.time()
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
    elapsed = time.time() - start
    usage = result.get("usage", {})
    return {
        "response": result["choices"][0]["message"]["content"],
        "tokens": usage.get("total_tokens", 0),
        "latency_ms": round(elapsed * 1000, 1),
    }


def call_openai_responses(
    prompt: str, model: str, api_key: str = None, base_url: str = None
) -> dict:
    """Call the OpenAI Responses API for GPT-5-class baselines."""
    import urllib.request

    api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
    base_url = (
        base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    ).rstrip("/")
    payload = json.dumps(
        {"model": model, "input": prompt, "max_output_tokens": 512}
    ).encode()
    req = urllib.request.Request(
        f"{base_url}/responses",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    start = time.time()
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
    elapsed = time.time() - start
    text = result.get("output_text", "")
    if not text:
        chunks = []
        for item in result.get("output", []):
            for part in item.get("content", []):
                if part.get("type") == "output_text":
                    chunks.append(part.get("text", ""))
        text = "".join(chunks)
    usage = result.get("usage", {})
    return {
        "response": text,
        "tokens": usage.get("total_tokens", 0),
        "latency_ms": round(elapsed * 1000, 1),
    }


def call_openai(
    prompt: str,
    model: str,
    api_key: str = None,
    base_url: str = None,
    api: str = "chat",
) -> dict:
    if api == "responses":
        return call_openai_responses(prompt, model, api_key, base_url)
    return call_openai_chat(prompt, model, api_key, base_url)


def call_openrouter(prompt: str, model: str, max_retries: int = 3) -> dict:
    """Call OpenRouter API with rate-limit retry (429 backoff)."""
    import urllib.request
    import urllib.error

    api_key = os.environ.get(
        "OPENROUTER_API_KEY", os.environ.get("OPENCODE_OPENROUTER_API_KEY", "")
    )
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 512,
            "temperature": 0,
        }
    ).encode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    for attempt in range(max_retries):
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers=headers,
        )
        try:
            start = time.time()
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
            elapsed = time.time() - start
            usage = result.get("usage", {})
            return {
                "response": result["choices"][0]["message"]["content"],
                "tokens": usage.get("total_tokens", 0),
                "latency_ms": round(elapsed * 1000, 1),
            }
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                time.sleep(wait)
                continue
            raise
    return {"response": "ERROR: rate limit exceeded", "tokens": 0, "latency_ms": 0}


def call_anthropic(prompt: str, model: str, api_key: str = None) -> dict:
    """Call the Anthropic Messages API (raw HTTP — matches the stdlib style here)."""
    import urllib.request

    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    payload = json.dumps(
        {
            "model": model,
            "max_tokens": 512,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    start = time.time()
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
    elapsed = time.time() - start
    # ponytail: first text block is the answer; refusals still carry a text block
    text = next(
        (b["text"] for b in result.get("content", []) if b["type"] == "text"), ""
    )
    usage = result.get("usage", {})
    return {
        "response": text,
        "tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
        "latency_ms": round(elapsed * 1000, 1),
    }


def main():
    parser = argparse.ArgumentParser(description="Run OpenMythos benchmark cases")
    parser.add_argument("--model", required=True, help="Model name")
    parser.add_argument(
        "--backend",
        default="ollama",
        choices=["ollama", "openai", "anthropic", "openrouter"],
    )
    parser.add_argument(
        "--governance-check",
        action="store_true",
        help="Enforce registry governance constraints (data class, pool, lifecycle)",
    )
    parser.add_argument(
        "--data-class",
        default="public",
        choices=["public", "internal", "confidential", "restricted"],
        help="Data classification for governance filtering",
    )
    parser.add_argument("--base-url", default=None, help="API base URL")
    parser.add_argument(
        "--api",
        default="chat",
        choices=["chat", "responses"],
        help="OpenAI API surface",
    )
    parser.add_argument("--output", default=None, help="Output JSONL path")
    parser.add_argument(
        "--corpus", type=Path, default=CORPUS_PATH, help="Corpus JSONL path"
    )
    parser.add_argument("--limit", type=int, default=None, help="Limit number of cases")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Append and skip case_ids already present in output",
    )
    parser.add_argument(
        "--num-predict", type=int, default=None, help="Ollama num_predict output cap"
    )
    parser.add_argument(
        "--timeout", type=int, default=120, help="HTTP timeout per case in seconds"
    )
    parser.add_argument(
        "--categories", nargs="+", default=None, help="Filter categories"
    )
    parser.add_argument(
        "--system", default=None, help="System prompt (ollama backend only)"
    )
    args = parser.parse_args()

    # Governance check: verify model is allowed for this data class
    if args.governance_check:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from model_registry import load_registry, eligible_models

        registry = load_registry()
        eligible = eligible_models(registry, data_class=args.data_class)
        eligible_names = {name for name, _ in eligible}
        model_short = args.model.split("/")[-1] if "/" in args.model else args.model
        # Match by full name, short name, or substring
        matched = (
            args.model in eligible_names
            or model_short in eligible_names
            or any(model_short in n or n in model_short for n in eligible_names)
        )
        if not matched and args.backend != "ollama":
            print(
                f"[GOVERNANCE BLOCK] Model '{args.model}' not eligible for data_class='{args.data_class}'"
            )
            print(f"  Eligible models: {', '.join(sorted(eligible_names))}")
            sys.exit(1)
        print(
            f"[GOVERNANCE OK] Model '{args.model}' eligible for data_class='{args.data_class}'"
        )

    cases = load_corpus(args.corpus)
    if args.categories:
        cases = [c for c in cases if c["category"] in args.categories]
    if args.limit:
        cases = cases[: args.limit]

    output_path = (
        Path(args.output)
        if args.output
        else REPO_ROOT / "traces" / f"{args.model.replace(':', '_')}.jsonl"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    done_ids = set()
    if args.resume and output_path.exists():
        with output_path.open() as existing:
            for line in existing:
                if line.strip():
                    done_ids.add(json.loads(line)["case_id"])
        cases = [c for c in cases if c["id"] not in done_ids]

    print(f"Running {len(cases)} cases against {args.model} ({args.backend})...")
    if done_ids:
        print(f"  resume: skipped {len(done_ids)} existing case(s)")

    mode = "a" if args.resume else "w"
    with open(output_path, mode, buffering=1) as f:
        for i, case in enumerate(cases):
            try:
                if args.backend == "ollama":
                    result = call_ollama(
                        case["prompt"],
                        args.model,
                        args.base_url or "http://localhost:11434",
                        args.num_predict,
                        args.timeout,
                        args.system,
                    )
                elif args.backend == "anthropic":
                    result = call_anthropic(case["prompt"], args.model)
                elif args.backend == "openrouter":
                    result = call_openrouter(case["prompt"], args.model)
                else:
                    result = call_openai(
                        case["prompt"], args.model, base_url=args.base_url, api=args.api
                    )
            except Exception as e:
                result = {"response": f"ERROR: {e}", "tokens": 0, "latency_ms": 0}

            entry = {
                "case_id": case["id"],
                "category": case["category"],
                "difficulty": case["difficulty"],
                "prompt": case["prompt"],
                "expected_behavior": case["expected_behavior"],
                "response": result["response"],
                "tokens": result["tokens"],
                "latency_ms": result["latency_ms"],
                "model": args.model,
                "backend": args.backend,
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            f.flush()

            if (i + 1) % 25 == 0:
                print(f"  [{i + 1}/{len(cases)}] done")

    print(f"\nResults written to: {output_path}")


if __name__ == "__main__":
    main()
