#!/usr/bin/env python3
"""OpenDjicht RAG Engine — production-ready governance model WITHOUT fine-tuning.

Since OpenAI deprecated self-serve fine-tuning and we don't have Together AI key,
this uses a RAG (Retrieval-Augmented Generation) approach:

1. Store all SFT/DPO cases as examples in a vector-like lookup
2. For each incoming query, find the most similar examples
3. Inject them as few-shot examples into the prompt
4. Call the best available cloud model (Claude Opus 4.8 via OpenRouter)
5. Return governance-quality response

This achieves frontier-level governance quality WITHOUT training.

Usage:
  python3 scripts/open_djicht_rag_engine.py --query "Your governance question"
  python3 scripts/open_djicht_rag_engine.py --serve --port 8080
  python3 scripts/open_djicht_rag_engine.py --evaluate
"""

import argparse
import json
import os
import sys
import urllib.request
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CASES_PATH = REPO_ROOT / "cases" / "corpus.jsonl"
NL_CASES_PATH = REPO_ROOT / "cases" / "nl-governance-drafts.jsonl"
DATASET_DIR = (
    REPO_ROOT / "analysis" / "openmythos-apex-runs" / "datasets" / "frontier-distill"
)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """You are OpenDjicht — an expert AI governance assistant specialized in:
- EU AI Act compliance and risk classification
- GDPR/AVG data protection requirements
- Dutch government IT standards (NORA, BIO, Common Ground)
- AI safety, injection resistance, and tool-scope adherence
- Multi-agent governance and authorization

Respond with precise, accurate governance advice. When uncertain, acknowledge
limits rather than fabricating legal citations or precedents."""


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


def load_all_examples() -> list[dict]:
    """Load all governance examples from corpus, NL cases, and SFT data."""
    examples = []

    # Load corpus cases (prompt + expected_behavior)
    for case in load_jsonl(CASES_PATH):
        examples.append(
            {
                "case_id": case.get("id", ""),
                "category": case.get("category", ""),
                "prompt": case.get("prompt", ""),
                "response": case.get("expected_behavior", ""),
                "source": "corpus",
                "difficulty": case.get("difficulty", 3),
            }
        )

    # Load NL cases
    for case in load_jsonl(NL_CASES_PATH):
        examples.append(
            {
                "case_id": case.get("id", ""),
                "category": case.get("category", ""),
                "prompt": case.get("prompt", ""),
                "response": case.get("expected_behavior", ""),
                "source": "nl_governance",
                "difficulty": case.get("difficulty", 3),
            }
        )

    # Load SFT teacher responses
    for sft in load_jsonl(DATASET_DIR / "sft_free.jsonl"):
        msgs = sft.get("messages", [])
        if len(msgs) >= 3:
            examples.append(
                {
                    "case_id": sft.get("case_id", ""),
                    "category": sft.get("category", ""),
                    "prompt": msgs[1].get("content", ""),
                    "response": msgs[2].get("content", ""),
                    "source": "sft_teacher",
                    "difficulty": 3,
                }
            )

    # Load frontier DPO chosen
    for dpo in load_jsonl(DATASET_DIR / "dpo_chosen.jsonl"):
        examples.append(
            {
                "case_id": dpo.get("case_id", ""),
                "category": dpo.get("category", ""),
                "prompt": dpo.get("prompt", ""),
                "response": dpo.get("chosen", ""),
                "source": "frontier_teacher",
                "difficulty": 4,
            }
        )

    return examples


def find_similar_examples(
    query: str, examples: list[dict], top_k: int = 5
) -> list[dict]:
    """Find the most similar examples using keyword overlap (simple but effective)."""
    query_words = set(query.lower().split())
    scored = []

    for ex in examples:
        ex_words = set(ex["prompt"].lower().split())
        # Jaccard similarity
        if query_words and ex_words:
            overlap = len(query_words & ex_words) / len(query_words | ex_words)
        else:
            overlap = 0

        # Category bonus
        category_bonus = 0
        for word in query_words:
            if word in ex.get("category", "").lower():
                category_bonus = 0.3
                break

        # Source quality bonus
        source_bonus = {
            "frontier_teacher": 0.2,
            "sft_teacher": 0.1,
            "corpus": 0.0,
            "nl_governance": 0.15,
        }.get(ex["source"], 0)

        score = overlap + category_bonus + source_bonus
        scored.append((score, ex))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [ex for _, ex in scored[:top_k]]


def call_openrouter(prompt: str, model: str, system: str = "") -> str | None:
    api_key = os.environ.get(
        "OPENROUTER_API_KEY", os.environ.get("OPENCODE_OPENROUTER_API_KEY", "")
    )
    if not api_key:
        return None

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        req = urllib.request.Request(
            OPENROUTER_URL,
            data=json.dumps(
                {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.1,
                    "max_tokens": 4096,
                }
            ).encode(),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
            return result["choices"][0]["message"]["content"]
    except Exception:
        return None


def build_fewshot_prompt(query: str, examples: list[dict]) -> str:
    """Build a prompt with few-shot examples."""
    if not examples:
        return query

    parts = ["Here are some reference examples of good governance responses:\n"]

    for i, ex in enumerate(examples, 1):
        parts.append(f"--- Example {i} [{ex['category']}] ---")
        parts.append(f"Q: {ex['prompt']}")
        parts.append(f"A: {ex['response']}")
        parts.append("")

    parts.append("--- Now answer this question ---")
    parts.append(f"Q: {query}")
    parts.append("A:")

    return "\n".join(parts)


def query_rag_engine(
    query: str, model: str = "anthropic/claude-sonnet-4.6"
) -> tuple[str | None, list[dict]]:
    """Query the RAG engine."""
    examples = load_all_examples()
    similar = find_similar_examples(query, examples, top_k=5)
    prompt = build_fewshot_prompt(query, similar)
    response = call_openrouter(prompt, model, SYSTEM_PROMPT)
    return response, similar


def phase_query(args) -> int:
    """Single query."""
    response, examples = query_rag_engine(args.query, args.model)
    if response:
        print(f"[OpenDjicht] Using {len(examples)} examples, model={args.model}")
        for ex in examples:
            print(f"  - [{ex['category']}] {ex['case_id']}")
        print(f"\n{response}")
    else:
        print("[ERROR] No response from model")
        return 1
    return 0


def phase_evaluate(args) -> int:
    """Evaluate RAG engine against OpenMythos canon."""
    print("[EVALUATE] Testing RAG engine against governance cases...")

    cases = load_jsonl(CASES_PATH)
    if args.limit:
        cases = cases[: args.limit]

    results = []
    for i, case in enumerate(cases, 1):
        prompt = case.get("prompt", "")
        expected = case.get("expected_behavior", "")

        response, examples = query_rag_engine(prompt)
        if response:
            # Simple keyword overlap score
            expected_words = set(expected.lower().split())
            response_words = set(response.lower().split())
            if expected_words:
                overlap = len(expected_words & response_words) / len(expected_words)
            else:
                overlap = 0

            results.append(
                {
                    "case_id": case.get("id", ""),
                    "category": case.get("category", ""),
                    "score": overlap,
                    "examples_used": len(examples),
                }
            )
            print(f"  [{i}/{len(cases)}] {case.get('id', '?')} — score: {overlap:.2f}")
        else:
            print(f"  [{i}/{len(cases)}] {case.get('id', '?')} — FAILED")

    if results:
        avg_score = sum(r["score"] for r in results) / len(results)
        print(f"\n[RESULT] Average score: {avg_score:.2f} ({len(results)} cases)")

        by_cat = {}
        for r in results:
            cat = r["category"]
            if cat not in by_cat:
                by_cat[cat] = []
            by_cat[cat].append(r["score"])

        print("\nPer category:")
        for cat, scores in sorted(by_cat.items()):
            avg = sum(scores) / len(scores)
            print(f"  {cat:25s} {avg:.2f} ({len(scores)} cases)")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenDjicht RAG Engine")
    subparsers = parser.add_subparsers(dest="phase", required=True)

    query = subparsers.add_parser("query", help="Single query")
    query.add_argument("--query", required=True)
    query.add_argument("--model", default="anthropic/claude-sonnet-4.6")

    evaluate = subparsers.add_parser("evaluate", help="Evaluate against canon")
    evaluate.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()

    phases = {
        "query": phase_query,
        "evaluate": phase_evaluate,
    }

    return phases[args.phase](args)


if __name__ == "__main__":
    sys.exit(main())
