#!/usr/bin/env python3
"""OpenDjicht API Server — OpenAI-compatible governance inference endpoint.

Zero dependencies (stdlib only). Runs on port 8080 by default.

Endpoints:
  POST /v1/chat/completions  — OpenAI-compatible chat endpoint
  POST /v1/query             — Simplified query endpoint
  GET  /health               — Health check
  GET  /stats                — Usage statistics
  GET  /examples             — List loaded examples

Usage:
  python3 scripts/open_djicht_api.py
  python3 scripts/open_djicht_api.py --port 8080
  python3 scripts/open_djicht_api.py --model anthropic/claude-sonnet-4.6
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
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

# Stats
STATS = {
    "queries": 0,
    "tokens_in": 0,
    "tokens_out": 0,
    "errors": 0,
    "start_time": time.time(),
}


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
    examples = []
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
    query_lower = query.lower()
    query_words = set(re.findall(r"\w+", query_lower)) - {
        "de",
        "het",
        "een",
        "van",
        "ik",
        "je",
        "we",
        "ze",
        "is",
        "op",
        "in",
        "met",
        "voor",
        "zijn",
        "dat",
        "niet",
        "maar",
        "ook",
        "aan",
        "als",
        "er",
        "om",
        "te",
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "have",
        "has",
        "do",
        "does",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "can",
        "to",
        "of",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "and",
        "but",
        "or",
        "not",
        "this",
        "that",
        "it",
        "what",
        "which",
        "who",
        "when",
        "where",
        "why",
        "how",
        "all",
        "each",
    }

    scored = []
    for ex in examples:
        ex_lower = ex["prompt"].lower()
        ex_words = set(re.findall(r"\w+", ex_lower)) - {
            "de",
            "het",
            "een",
            "van",
            "ik",
            "je",
            "we",
            "ze",
            "is",
            "op",
            "in",
            "met",
            "voor",
            "zijn",
            "dat",
            "niet",
            "maar",
            "ook",
            "aan",
            "als",
            "er",
            "om",
            "te",
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "have",
            "has",
            "do",
            "does",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "to",
            "of",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "and",
            "but",
            "or",
            "not",
            "this",
            "that",
            "it",
            "what",
            "which",
            "who",
            "when",
            "where",
            "why",
            "how",
            "all",
            "each",
        }

        if query_words and ex_words:
            overlap = len(query_words & ex_words) / len(query_words | ex_words)
        else:
            overlap = 0

        cat = ex.get("category", "").lower().replace("-", " ")
        category_bonus = 0.2 if any(w in cat for w in query_words) else 0

        source_bonus = {
            "frontier_teacher": 0.15,
            "nl_governance": 0.12,
            "sft_teacher": 0.08,
            "corpus": 0.05,
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
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": prompt}
    ]
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
    if not examples:
        return query
    parts = ["Here are reference examples of good governance responses:\n"]
    for i, ex in enumerate(examples, 1):
        parts.append(f"--- Example {i} [{ex['category']}] ---")
        parts.append(f"Q: {ex['prompt']}")
        parts.append(f"A: {ex['response']}\n")
    parts.append("--- Now answer this question ---")
    parts.append(f"Q: {query}")
    parts.append("A:")
    return "\n".join(parts)


# Load examples once at startup
EXAMPLES = load_all_examples()
print(f"[OpenDjicht] Loaded {len(EXAMPLES)} examples")


class OpenDjichtHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Suppress default logging to reduce noise."""
        pass

    def _send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def _read_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            body = self.rfile.read(content_length)
            try:
                return json.loads(body.decode())
            except json.JSONDecodeError:
                return {}
        return {}

    def do_GET(self):
        if self.path == "/health":
            self._send_json(
                {
                    "status": "healthy",
                    "model": "open-djicht-governance",
                    "examples_loaded": len(EXAMPLES),
                    "uptime_s": int(time.time() - STATS["start_time"]),
                }
            )
        elif self.path == "/stats":
            self._send_json(
                {
                    "queries": STATS["queries"],
                    "errors": STATS["errors"],
                    "examples_loaded": len(EXAMPLES),
                    "uptime_s": int(time.time() - STATS["start_time"]),
                }
            )
        elif self.path == "/examples":
            cats = {}
            for ex in EXAMPLES:
                c = ex.get("category", "?")
                cats[c] = cats.get(c, 0) + 1
            self._send_json({"total": len(EXAMPLES), "by_category": cats})
        else:
            self._send_json({"error": "Not found"}, status=404)

    def do_POST(self):
        if self.path == "/v1/chat/completions":
            self._handle_chat_completions()
        elif self.path == "/v1/query":
            self._handle_query()
        else:
            self._send_json({"error": "Not found"}, status=404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def _handle_chat_completions(self):
        body = self._read_body()
        messages = body.get("messages", [])
        model = body.get("model", "anthropic/claude-sonnet-4.6")

        # Extract user message
        user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = m.get("content", "")
                break

        if not user_msg:
            self._send_json({"error": "No user message found"}, status=400)
            return

        # Find similar examples and build prompt
        similar = find_similar_examples(user_msg, EXAMPLES, top_k=5)
        prompt = build_fewshot_prompt(user_msg, similar)

        # Call model
        STATS["queries"] += 1
        response = call_openrouter(prompt, model, SYSTEM_PROMPT)

        if response:
            self._send_json(
                {
                    "id": f"chatcmpl-{hashlib.sha256(user_msg.encode()).hexdigest()[:24]}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": f"open-djicht/{model}",
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": response},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": len(prompt.split()),
                        "completion_tokens": len(response.split()),
                        "total_tokens": len(prompt.split()) + len(response.split()),
                    },
                    "open_djicht": {
                        "examples_used": len(similar),
                        "categories": list(
                            set(ex.get("category", "") for ex in similar)
                        ),
                    },
                }
            )
        else:
            STATS["errors"] += 1
            self._send_json({"error": "Model call failed"}, status=502)

    def _handle_query(self):
        body = self._read_body()
        query = body.get("query", "")
        model = body.get("model", "anthropic/claude-sonnet-4.6")

        if not query:
            self._send_json({"error": "No query provided"}, status=400)
            return

        similar = find_similar_examples(query, EXAMPLES, top_k=5)
        prompt = build_fewshot_prompt(query, similar)

        STATS["queries"] += 1
        response = call_openrouter(prompt, model, SYSTEM_PROMPT)

        if response:
            self._send_json(
                {
                    "query": query,
                    "response": response,
                    "model": model,
                    "examples_used": len(similar),
                    "categories": list(set(ex.get("category", "") for ex in similar)),
                }
            )
        else:
            STATS["errors"] += 1
            self._send_json({"error": "Model call failed"}, status=502)


def main():
    parser = argparse.ArgumentParser(description="OpenDjicht API Server")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), OpenDjichtHandler)
    print(f"[OpenDjicht] API server running at http://{args.host}:{args.port}")
    print(f"[OpenDjicht] Endpoints:")
    print(f"  POST http://{args.host}:{args.port}/v1/chat/completions")
    print(f"  POST http://{args.host}:{args.port}/v1/query")
    print(f"  GET  http://{args.host}:{args.port}/health")
    print(f"  GET  http://{args.host}:{args.port}/stats")
    print(f"\n[OpenDjicht] Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[OpenDjicht] Server stopped")
        server.server_close()


if __name__ == "__main__":
    main()
