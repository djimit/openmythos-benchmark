#!/usr/bin/env python3
"""Together AI fine-tuning orchestrator for OpenDjicht-1.

Since OpenAI deprecated self-serve fine-tuning, Together AI is the best alternative:
- Supports Qwen3-32B, Llama-4, DeepSeek fine-tuning
- Pay-per-token pricing (no GPU reservation needed)
- REST API for upload, train, deploy
- Serverless inference after training

Alternative: Azure AI Foundry (if you have Microsoft subscription)

Usage:
  python3 scripts/together_training.py upload --dataset analysis/.../sft_combined.jsonl
  python3 scripts/together_train.py train --file-id file_xxx --model Qwen/Qwen3-32B
  python3 scripts/together_training.py status --job-id xxx
  python3 scripts/together_training.py list-models
"""

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DATASET_DIR = (
    REPO_ROOT / "analysis" / "openmythos-apex-runs" / "datasets" / "frontier-distill"
)
TOGETHER_URL = "https://api.together.xyz/v1"

# Supported fine-tuning models on Together AI
SUPPORTED_MODELS = {
    "qwen3-32b": {
        "id": "Qwen/Qwen3-32B",
        "context": 131072,
        "cost_per_1m_tokens": 0.80,  # estimated
        "best_for": "Governance reasoning, NL understanding",
    },
    "qwen3-72b": {
        "id": "Qwen/Qwen3-72B",
        "context": 131072,
        "cost_per_1m_tokens": 1.50,
        "best_for": "Best quality, slower",
    },
    "llama-4-maverick": {
        "id": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "context": 1000000,
        "cost_per_1m_tokens": 1.00,
        "best_for": "Long context, agentic",
    },
    "deepseek-v3": {
        "id": "deepseek-ai/DeepSeek-V3-0324",
        "context": 131072,
        "cost_per_1m_tokens": 0.50,
        "best_for": "Cost-effective reasoning",
    },
    "gpt-oss-120b": {
        "id": "openai/gpt-oss-120b",
        "context": 131072,
        "cost_per_1m_tokens": 0.30,
        "best_for": "Open-weight, cheap",
    },
}


def get_api_key() -> str:
    """Get Together AI API key."""
    key = os.environ.get("TOGETHER_API_KEY", "")
    if not key:
        print("ERROR: TOGETHER_API_KEY not set")
        print("  Get one at: https://api.together.xyz/settings/api-keys")
        sys.exit(1)
    return key


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


def together_request(
    endpoint: str, payload: dict | None = None, method: str = "GET"
) -> dict:
    """Make a Together AI API request."""
    api_key = get_api_key()
    url = f"{TOGETHER_URL}{endpoint}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return {"error": True, "status": e.code, "message": body}
    except Exception as e:
        return {"error": True, "message": str(e)}


def phase_list_models(args) -> int:
    """List available fine-tuning models on Together AI."""
    print("=== Together AI Fine-tuning Models ===")
    for name, info in SUPPORTED_MODELS.items():
        print(
            f"  {name:20s} {info['id']:50s} ctx={info['context']:>10,}  ~${info['cost_per_1m_tokens']:.2f}/1M"
        )
        print(f"    Best for: {info['best_for']}")
    return 0


def phase_upload(args) -> int:
    """Upload training file to Together AI."""
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"ERROR: Dataset not found: {dataset_path}")
        return 1

    rows = load_jsonl(dataset_path)
    valid = sum(1 for r in rows if "messages" in r and isinstance(r["messages"], list))

    print(f"[UPLOAD] {dataset_path.name} — {valid}/{len(rows)} valid SFT samples")

    if args.dry_run:
        print("[DRY RUN] Would upload to Together AI")
        return 0

    # Together AI uses OpenAI-compatible file upload
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

    api_key = get_api_key()
    req = urllib.request.Request(
        f"{TOGETHER_URL}/files",
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
                f"[NEXT] Train: python3 scripts/together_training.py train --file-id {file_id} --model qwen3-32b"
            )
            return 0
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"[ERROR] Upload failed: {e.code} — {body}")
        return 1


def phase_train(args) -> int:
    """Launch fine-tuning job on Together AI."""
    file_id = args.file_id
    model_name = args.model
    epochs = args.epochs or 3

    if model_name not in SUPPORTED_MODELS:
        print(f"ERROR: Unknown model: {model_name}")
        print(f"  Available: {', '.join(SUPPORTED_MODELS.keys())}")
        return 1

    model_info = SUPPORTED_MODELS[model_name]

    print(f"[TRAIN] Model={model_info['id']}, File={file_id}, Epochs={epochs}")
    print(
        f"  Estimated cost: ${model_info['cost_per_1m_tokens'] * epochs * 0.5:.2f}-{model_info['cost_per_1m_tokens'] * epochs * 2:.2f}"
    )

    if args.dry_run:
        print("[DRY RUN] Would launch training job")
        return 0

    result = together_request(
        "/fine-tunes",
        {
            "training_file": file_id,
            "model": model_info["id"],
            "n_epochs": epochs,
            "batch_size": "auto",
            "learning_rate": 1e-5,
            "suffix": "open-djicht-governance",
            "wandb_api_key": os.environ.get("WANDB_API_KEY", ""),
        },
        method="POST",
    )

    if result.get("error"):
        print(f"[ERROR] Training launch failed: {result.get('message', 'unknown')}")
        return 1

    job_id = result.get("id", "unknown")
    print(f"[LAUNCHED] Job ID: {job_id}")
    print(
        f"[STATUS] Check: python3 scripts/together_training.py status --job-id {job_id}"
    )

    # Save job info
    job_info = {
        "job_id": job_id,
        "model": model_info["id"],
        "file_id": file_id,
        "status": result.get("status", "queued"),
        "launched_at": datetime.now(timezone.utc).isoformat(),
    }
    job_path = DATASET_DIR / f"together_job_{job_id}.json"
    job_path.write_text(json.dumps(job_info, indent=2))

    return 0


def phase_status(args) -> int:
    """Check training job status."""
    job_id = args.job_id
    result = together_request(f"/fine-tunes/{job_id}")

    if result.get("error"):
        print(f"[ERROR] Status check failed: {result.get('message', 'unknown')}")
        return 1

    status = result.get("status", "unknown")
    model = result.get("model", "")
    fine_tuned = result.get("fine_tuned_model", "")

    print(f"[STATUS] Job: {job_id}")
    print(f"  Status: {status}")
    print(f"  Model: {model}")
    if fine_tuned:
        print(f"  Fine-tuned model: {fine_tuned}")

    if status == "completed" and fine_tuned:
        print(f"\n[DONE] Model ready: {fine_tuned}")
        print(f"[INFERENCE] Use via Together AI API or deploy to serverless endpoint")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Together AI fine-tuning for OpenDjicht-1"
    )
    subparsers = parser.add_subparsers(dest="phase", required=True)

    subparsers.add_parser("list-models", help="List available fine-tuning models")

    upload = subparsers.add_parser("upload", help="Upload training data")
    upload.add_argument("--dataset", required=True)
    upload.add_argument("--dry-run", action="store_true")

    train = subparsers.add_parser("train", help="Launch training job")
    train.add_argument("--file-id", required=True)
    train.add_argument(
        "--model", default="qwen3-32b", choices=list(SUPPORTED_MODELS.keys())
    )
    train.add_argument("--epochs", type=int, default=3)
    train.add_argument("--dry-run", action="store_true")

    status = subparsers.add_parser("status", help="Check job status")
    status.add_argument("--job-id", required=True)

    args = parser.parse_args()

    phases = {
        "list-models": phase_list_models,
        "upload": phase_upload,
        "train": phase_train,
        "status": phase_status,
    }

    return phases[args.phase](args)


if __name__ == "__main__":
    sys.exit(main())
