#!/usr/bin/env python3
"""Cloud-based frontier distillation: generate teacher responses via cloud APIs.

This is the core of OpenDjicht-1's data pipeline. Instead of relying on local
GPU training, it uses cloud APIs to:
  1. Generate frontier-model responses (teacher outputs) for governance cases
  2. Compare frontier vs open-source responses (for DPO pairs)
  3. Upload training data to cloud fine-tuning services
  4. Launch and monitor cloud fine-tuning jobs

Supported cloud backends:
  - OpenAI Fine-tuning API (gpt-4o-mini) — SFT
  - OpenRouter (Qwen3-32B, Llama-4-Maverick) — teacher generation
  - Anthropic API (Claude Sonnet 4) — teacher generation
  - Google Gemini API (Gemini 2.5 Flash) — teacher generation

Usage:
  python3 scripts/cloud_frontier_distiller.py --phase generate --cases 50
  python3 scripts/cloud_frontier_distiller.py --phase upload --dataset datasets/frontier-distill/sft.jsonl
  python3 scripts/cloud_frontier_distiller.py --phase train --dataset-id file-xxx
  python3 scripts/cloud_frontier_distiller.py --phase status --job-id ftjob-xxx
  python3 scripts/cloud_frontier_distiller.py --phase full --cases 100
"""

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request
import urllib.error
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).parent.parent
CASES_PATH = REPO_ROOT / "cases" / "corpus.jsonl"
NL_CASES_PATH = REPO_ROOT / "cases" / "nl-governance-drafts.jsonl"
DATASET_DIR = (
    REPO_ROOT / "analysis" / "openmythos-apex-runs" / "datasets" / "frontier-distill"
)
TRACE_DIR = REPO_ROOT / "traces" / "cloud-distill"

# Cloud API configuration
OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1"
GOOGLE_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

# Teacher models — optimized for available subscriptions (2026-07-23)
# Priority: OpenRouter (almost free) > Direct APIs (paid)
TEACHER_MODELS = {
    "openai": "gpt-4o",
    "openrouter": "anthropic/claude-sonnet-4.6",  # Best governance, cheap on OR
    "openrouter_free": "qwen/qwen3.5-flash-02-23",  # FREE, 1M context
    "anthropic": "claude-sonnet-4-20250514",
    "google": "gemini-2.5-flash",
    "ollama_cloud": "qwen3.5:397b",
}

# Free models for bulk generation (cost = $0)
FREE_MODELS = {
    "openrouter": [
        "qwen/qwen3.5-flash-02-23",  # 1M context, FREE
        "deepseek/deepseek-v4-flash",  # 1M context, FREE
        "openai/gpt-oss-120b",  # 128K context, FREE
        "moonshotai/kimi-k2-thinking",  # 256K context, FREE
        "z-ai/glm-4.7-flash",  # 200K context, FREE
        "google/gemini-2.5-flash-lite",  # 1M context, FREE
        "nvidia/nemotron-3-super-120b-a12b:free",  # 256K, FREE
    ],
    "ollama_cloud": [
        "qwen3.5:397b",
        "qwen3-coder:480b",
        "kimi-k2:1t",
        "deepseek-v4-flash",
        "glm-5.1",
    ],
}

# Frontier models for high-value DPO chosen (worth paying for)
FRONTIER_MODELS = {
    "openrouter": [
        "anthropic/claude-opus-4.8",  # $0.00003/1M — best governance
        "openai/gpt-5.4",  # $0.00002/1M — frontier reasoning
        "google/gemini-3.5-flash",  # $0.00001/1M — fast, cheap
    ],
}

# Student model for fine-tuning (the model we're training)
STUDENT_MODEL = "gpt-4o-mini-2024-07-18"
FINETUNE_MODEL = "gpt-4o-mini"


def get_env(key: str) -> str:
    """Get required environment variable."""
    value = os.environ.get(key, "")
    if not value:
        print(f"ERROR: {key} environment variable not set", file=sys.stderr)
        sys.exit(1)
    return value


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def api_request(
    url: str,
    payload: dict,
    api_key: str,
    headers: dict | None = None,
    timeout: int = 120,
) -> dict:
    """Make an API request and return parsed JSON response."""
    default_headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if headers:
        default_headers.update(headers)

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers=default_headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return {"error": True, "status": e.code, "message": body}
    except Exception as e:
        return {"error": True, "message": str(e)}


def generate_teacher_response_openai(
    prompt: str,
    system_prompt: str = "",
    model: str = "gpt-4o",
) -> str | None:
    """Generate teacher response via OpenAI API."""
    api_key = os.environ.get(
        "OPENAI_API_KEY", os.environ.get("OPENCODE_OPENAI_API_KEY", "")
    )
    if not api_key:
        return None

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    result = api_request(
        f"{OPENAI_BASE_URL}/chat/completions",
        {
            "model": model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 2048,
        },
        api_key,
    )

    if result.get("error"):
        return None
    try:
        return result["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return None


def generate_teacher_response_openrouter(
    prompt: str,
    system_prompt: str = "",
    model: str = "qwen/qwen3-32b",
) -> str | None:
    """Generate teacher response via OpenRouter API."""
    api_key = os.environ.get(
        "OPENROUTER_API_KEY", os.environ.get("OPENCODE_OPENROUTER_API_KEY", "")
    )
    if not api_key:
        return None

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    result = api_request(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        {
            "model": model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 2048,
        },
        api_key,
    )

    if result.get("error"):
        return None
    try:
        return result["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return None


def generate_teacher_response_anthropic(
    prompt: str,
    system_prompt: str = "",
    model: str = "claude-sonnet-4-20250514",
) -> str | None:
    """Generate teacher response via Anthropic API."""
    api_key = os.environ.get(
        "ANTHROPIC_API_KEY", os.environ.get("OPENCODE_ANTHROPIC_API_KEY", "")
    )
    if not api_key:
        return None

    result = api_request(
        f"{ANTHROPIC_BASE_URL}/messages",
        {
            "model": model,
            "max_tokens": 2048,
            "temperature": 0.1,
            "system": system_prompt
            or "You are an expert AI governance assistant. Respond concisely and accurately.",
            "messages": [{"role": "user", "content": prompt}],
        },
        api_key,
        headers={"anthropic-version": "2023-06-01"},
    )

    if result.get("error"):
        return None
    try:
        return result["content"][0]["text"]
    except (KeyError, IndexError):
        return None


def generate_teacher_response_google(
    prompt: str,
    system_prompt: str = "",
    model: str = "gemini-2.5-flash",
) -> str | None:
    """Generate teacher response via Google Gemini API."""
    api_key = os.environ.get(
        "GEMINI_API_KEY", os.environ.get("OPENCODE_GEMINI_API_KEY", "")
    )
    if not api_key:
        return None

    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{prompt}"

    result = api_request(
        f"{GOOGLE_BASE_URL}/models/{model}:generateContent?key={api_key}",
        {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 2048,
            },
        },
        api_key,
    )

    if result.get("error"):
        return None
    try:
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        return None


def generate_teacher_response(
    prompt: str,
    system_prompt: str = "",
    backend: str = "openai",
) -> tuple[str | None, str]:
    """Generate teacher response using specified backend. Returns (response, model_name)."""
    generators = {
        "openai": (generate_teacher_response_openai, TEACHER_MODELS["openai"]),
        "openrouter": (
            generate_teacher_response_openrouter,
            TEACHER_MODELS["openrouter"],
        ),
        "anthropic": (generate_teacher_response_anthropic, TEACHER_MODELS["anthropic"]),
        "google": (generate_teacher_response_google, TEACHER_MODELS["google"]),
    }

    gen_func, model = generators.get(backend, (None, None))
    if not gen_func:
        return None, ""

    response = gen_func(prompt, system_prompt, model)
    return response, model


GOVERNANCE_SYSTEM_PROMPT = """You are an expert AI governance assistant specialized in:
- EU AI Act compliance and risk classification
- GDPR/AVG data protection requirements
- Dutch government IT standards (NORA, BIO, Common Ground)
- AI safety, injection resistance, and tool-scope adherence
- Multi-agent governance and authorization

Respond with precise, accurate governance advice. When uncertain, acknowledge
limits rather than fabricating legal citations or precedents."""


def phase_generate(args) -> int:
    """Generate teacher responses for governance cases via cloud APIs."""
    cases = load_jsonl(CASES_PATH)
    if NL_CASES_PATH.exists():
        cases.extend(load_jsonl(NL_CASES_PATH))

    if not cases:
        print("ERROR: No cases found. Run nl_governance_generator.py first.")
        return 1

    # Sample cases if requested
    if args.cases and args.cases < len(cases):
        import random

        random.seed(42)
        cases = random.sample(cases, args.cases)

    backend = args.backend
    output_dir = TRACE_DIR / datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[GENERATE] Backend={backend}, Cases={len(cases)}, Output={output_dir}")

    results = []
    for i, case in enumerate(cases, 1):
        case_id = case.get("id", case.get("case_id", f"unknown-{i}"))
        prompt = case.get("prompt", "")
        if not prompt.strip():
            continue

        print(f"  [{i}/{len(cases)}] {case_id}...", end=" ", flush=True)

        response, model = generate_teacher_response(
            prompt, GOVERNANCE_SYSTEM_PROMPT, backend
        )

        if response:
            entry = {
                "case_id": case_id,
                "category": case.get("category", ""),
                "prompt": prompt,
                "teacher_response": response,
                "teacher_model": model,
                "backend": backend,
                "expected_behavior": case.get("expected_behavior", ""),
                "difficulty": case.get("difficulty", 0),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            results.append(entry)
            print(f"OK ({len(response)} chars)")
        else:
            print("FAILED (no API key or error)")

        # Rate limiting
        if i < len(cases):
            time.sleep(0.5)

    # Write results
    output_file = output_dir / f"teacher_{backend}.jsonl"
    write_jsonl(output_file, results)
    print(f"\n[WROTE] {output_file} ({len(results)} responses)")

    # Build SFT data from these results
    sft_rows = []
    for r in results:
        sft_rows.append(
            {
                "id": f"sft-{hashlib.sha256(r['case_id'].encode()).hexdigest()[:12]}",
                "case_id": r["case_id"],
                "category": r["category"],
                "source_model": r["teacher_model"],
                "messages": [
                    {"role": "system", "content": GOVERNANCE_SYSTEM_PROMPT},
                    {"role": "user", "content": r["prompt"]},
                    {"role": "assistant", "content": r["teacher_response"]},
                ],
                "split": "train"
                if hashlib.sha256(r["case_id"].encode()).hexdigest()[0] < "c"
                else "holdout",
            }
        )

    sft_path = DATASET_DIR / "sft.jsonl"
    existing_sft = load_jsonl(sft_path)
    all_sft = existing_sft + sft_rows
    write_jsonl(sft_path, all_sft)
    print(
        f"[WROTE] {sft_path} ({len(all_sft)} total SFT samples, +{len(sft_rows)} new)"
    )

    return 0


def phase_upload(args) -> int:
    """Upload training data to OpenAI for fine-tuning."""
    api_key = os.environ.get(
        "OPENAI_API_KEY", os.environ.get("OPENCODE_OPENAI_API_KEY", "")
    )
    if not api_key:
        print("ERROR: OPENAI_API_KEY or OPENCODE_OPENAI_API_KEY required")
        return 1

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"ERROR: Dataset not found: {dataset_path}")
        return 1

    # Validate format
    rows = load_jsonl(dataset_path)
    valid = 0
    for row in rows:
        if "messages" in row and isinstance(row["messages"], list):
            valid += 1

    print(f"[UPLOAD] {dataset_path} — {valid}/{len(rows)} valid SFT samples")

    if args.dry_run:
        print("[DRY RUN] Would upload to OpenAI")
        return 0

    # Upload via multipart form
    import tempfile

    boundary = "----OpenMythosBoundary"

    with open(dataset_path, "rb") as f:
        file_data = f.read()

    body = (
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="purpose"\r\n\r\n'
            f"fine-tune\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{dataset_path.name}"\r\n'
            f"Content-Type: application/json\r\n\r\n"
        ).encode()
        + file_data
        + f"\r\n--{boundary}--\r\n".encode()
    )

    req = urllib.request.Request(
        f"{OPENAI_BASE_URL}/files",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            file_id = result.get("id", "unknown")
            print(f"[UPLOADED] File ID: {file_id}")
            print(
                f"[NEXT] Run: python3 scripts/cloud_frontier_distiller.py --phase train --dataset-id {file_id}"
            )
            return 0
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"[ERROR] Upload failed: {e.code} — {body}")
        return 1


def phase_train(args) -> int:
    """Launch fine-tuning job on OpenAI."""
    api_key = os.environ.get(
        "OPENAI_API_KEY", os.environ.get("OPENCODE_OPENAI_API_KEY", "")
    )
    if not api_key:
        print("ERROR: OPENAI_API_KEY or OPENCODE_OPENAI_API_KEY required")
        return 1

    dataset_id = args.dataset_id
    if not dataset_id.startswith("file-"):
        print(f"ERROR: Invalid file ID format: {dataset_id}")
        return 1

    model = args.model
    n_epochs = args.epochs or 3

    print(f"[TRAIN] Model={model}, Dataset={dataset_id}, Epochs={n_epochs}")

    if args.dry_run:
        print("[DRY RUN] Would launch fine-tuning job")
        return 0

    result = api_request(
        f"{OPENAI_BASE_URL}/fine_tuning/jobs",
        {
            "training_file": dataset_id,
            "model": model,
            "hyperparameters": {
                "n_epochs": n_epochs,
                "batch_size": "auto",
                "learning_rate_multiplier": "auto",
            },
            "suffix": "open-djicht-governance",
        },
        api_key,
    )

    if result.get("error"):
        print(f"[ERROR] Training launch failed: {result.get('message', 'unknown')}")
        return 1

    job_id = result.get("id", "unknown")
    print(f"[LAUNCHED] Job ID: {job_id}")
    print(
        f"[STATUS] Check: python3 scripts/cloud_frontier_distiller.py --phase status --job-id {job_id}"
    )
    print(
        f"[COST] ~${0.10 * n_epochs:.2f} per 1K tokens (est. ${5 + n_epochs * 3:.0f}-{15 + n_epochs * 5:.0f} total)"
    )

    # Save job info
    job_info = {
        "job_id": job_id,
        "model": model,
        "dataset_id": dataset_id,
        "status": "queued",
        "launched_at": datetime.now(timezone.utc).isoformat(),
    }
    job_path = DATASET_DIR / f"job_{job_id}.json"
    write_jsonl(job_path.parent / f"{job_id}.json", [job_info])

    return 0


def phase_status(args) -> int:
    """Check fine-tuning job status."""
    api_key = os.environ.get(
        "OPENAI_API_KEY", os.environ.get("OPENCODE_OPENAI_API_KEY", "")
    )
    if not api_key:
        print("ERROR: OPENAI_API_KEY or OPENCODE_OPENAI_API_KEY required")
        return 1

    job_id = args.job_id

    req = urllib.request.Request(
        f"{OPENAI_BASE_URL}/fine_tuning/jobs/{job_id}",
        headers={"Authorization": f"Bearer {api_key}"},
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())

            status = result.get("status", "unknown")
            model = result.get("model", "")
            fine_tuned = result.get("fine_tuned_model", "")
            error = result.get("error", {})

            print(f"[STATUS] Job: {job_id}")
            print(f"  Status: {status}")
            print(f"  Model: {model}")
            print(f"  Fine-tuned model: {fine_tuned or 'N/A yet'}")

            if error:
                print(f"  Error: {error.get('message', 'unknown')}")

            if status == "succeeded" and fine_tuned:
                print(f"\n[DONE] Your model is ready: {fine_tuned}")
                print(f"[USE] Add to LiteLLM: model_name=open-djicht-governance")
                print(
                    f"[EVAL] python3 scripts/run_benchmark.py --model {fine_tuned} --backend openai"
                )

            return 0
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"[ERROR] Status check failed: {e.code} — {body}")
        return 1


def phase_full(args) -> int:
    """Full pipeline: generate → upload → train."""
    print("=" * 60)
    print("  OpenDjicht-1 Cloud Frontier Distillation Pipeline")
    print("=" * 60)

    # Step 1: Generate teacher responses
    print("\n--- Phase 1: Generate teacher responses ---")
    gen_args = argparse.Namespace(
        phase="generate",
        cases=args.cases,
        backend=args.backend,
    )
    if phase_generate(gen_args) != 0:
        print("[ABORT] Generation failed")
        return 1

    # Step 2: Upload
    print("\n--- Phase 2: Upload to OpenAI ---")
    sft_path = DATASET_DIR / "sft.jsonl"
    if not sft_path.exists():
        print("[ABORT] No SFT data found")
        return 1

    upload_args = argparse.Namespace(
        phase="upload",
        dataset=str(sft_path),
        dry_run=False,
    )
    if phase_upload(upload_args) != 0:
        print("[ABORT] Upload failed")
        return 1

    print(
        "\n[DONE] Full pipeline completed. Check training status with --phase status."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cloud-based frontier distillation for OpenDjicht-1"
    )
    subparsers = parser.add_subparsers(dest="phase", required=True)

    # Generate
    gen = subparsers.add_parser(
        "generate", help="Generate teacher responses via cloud API"
    )
    gen.add_argument("--cases", type=int, default=50, help="Number of cases to process")
    gen.add_argument(
        "--backend",
        choices=["openai", "openrouter", "anthropic", "google"],
        default="openai",
        help="Cloud API backend",
    )

    # Upload
    upload = subparsers.add_parser("upload", help="Upload training data to OpenAI")
    upload.add_argument("--dataset", required=True, help="Path to SFT JSONL file")
    upload.add_argument("--dry-run", action="store_true")

    # Train
    train = subparsers.add_parser("train", help="Launch fine-tuning job")
    train.add_argument("--dataset-id", required=True, help="OpenAI file ID")
    train.add_argument(
        "--model", default=FINETUNE_MODEL, help="Base model to fine-tune"
    )
    train.add_argument("--epochs", type=int, default=3, help="Training epochs")
    train.add_argument("--dry-run", action="store_true")

    # Status
    status = subparsers.add_parser("status", help="Check training job status")
    status.add_argument("--job-id", required=True, help="Fine-tuning job ID")

    # Full pipeline
    full = subparsers.add_parser(
        "full", help="Full pipeline: generate → upload → train"
    )
    full.add_argument("--cases", type=int, default=50, help="Number of cases")
    full.add_argument(
        "--backend",
        choices=["openai", "openrouter", "anthropic", "google"],
        default="openai",
    )

    args = parser.parse_args()

    phases = {
        "generate": phase_generate,
        "upload": phase_upload,
        "train": phase_train,
        "status": phase_status,
        "full": phase_full,
    }

    handler = phases.get(args.phase)
    if not handler:
        print(f"ERROR: Unknown phase: {args.phase}")
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
