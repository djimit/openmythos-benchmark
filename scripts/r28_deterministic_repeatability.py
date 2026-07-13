#!/usr/bin/env python3
"""Measure exact subject-response repeatability under deterministic Ollama options."""

import argparse
import hashlib
import json
import time
import urllib.request
from pathlib import Path

from oracle_score import load_corpus, merged_case, score
from r20_lora_sft_pilot import CORPUS_PATH, REPORT_DIR, load_jsonl
from r27_secret_policy_ab import MANIFESTS, MODEL, OLLAMA_URL, percentile, sha256

REPETITIONS = 3
OPTIONS = {"temperature": 0, "seed": 0, "num_predict": 1024}


def decide(complete: bool, cases: int, response_stable: bool, oracle_stable: bool) -> dict:
    reasons = []
    if not complete:
        reasons.append("incomplete-evidence")
    if cases != 8:
        reasons.append("unexpected-case-count")
    if not response_stable:
        reasons.append("response-instability")
    if not oracle_stable:
        reasons.append("oracle-instability")
    return {"status": "pass" if not reasons else "fail", "reasons": reasons}


def generate(prompt: str) -> tuple[str, int, str | None]:
    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": OPTIONS,
    }).encode()
    request = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            body = json.load(response)
        return str(body.get("response", "")), round((time.time() - started) * 1000), None
    except Exception as exc:
        return "", round((time.time() - started) * 1000), f"{type(exc).__name__}: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=REPORT_DIR / "apex-r28-deterministic-repeatability.json")
    parser.add_argument("--markdown-output", type=Path, default=REPORT_DIR / "APEX_R28_DETERMINISTIC_REPEATABILITY.md")
    args = parser.parse_args()

    corpus = load_corpus(CORPUS_PATH)
    cases = []
    for path in MANIFESTS:
        for row in load_jsonl(path):
            if row["metadata"]["category"] != "canary":
                continue
            case_id = str(row["metadata"]["case_id"])
            corpus[case_id] = merged_case({**row, "case_id": case_id}, corpus)
            cases.append({"case_id": case_id, "category": "canary", "prompt": row["prompt"]})

    results = []
    for repetition in range(1, REPETITIONS + 1):
        for case in cases:
            response, latency_ms, error = generate(case["prompt"])
            oracle = score(merged_case({**case, "response": response}, corpus))
            results.append({
                **case,
                "repetition": repetition,
                "response": response,
                "response_sha256": hashlib.sha256(response.encode()).hexdigest(),
                "latency_ms": latency_ms,
                "error": error,
                "oracle_type": oracle["oracle_type"],
                "oracle_applicable": oracle["oracle_applicable"],
                "oracle_pass": oracle["oracle_pass"],
                "oracle_reason": oracle["oracle_reason"],
            })

    stability = []
    for case in cases:
        repeated = [row for row in results if row["case_id"] == case["case_id"]]
        hashes = sorted({row["response_sha256"] for row in repeated})
        outcomes = sorted({row["oracle_pass"] for row in repeated})
        stability.append({
            "case_id": case["case_id"],
            "response_stable": len(hashes) == 1,
            "oracle_stable": len(outcomes) == 1,
            "unique_response_hashes": hashes,
            "oracle_outcomes": outcomes,
        })

    complete = (
        len(cases) == 8
        and len(results) == 8 * REPETITIONS
        and not any(row["error"] for row in results)
        and all(row["oracle_applicable"] for row in results)
    )
    response_stable = all(row["response_stable"] for row in stability)
    oracle_stable = all(row["oracle_stable"] for row in stability)
    latencies = [row["latency_ms"] for row in results]
    report = {
        "schema_version": 1,
        "model": MODEL,
        "options": OPTIONS,
        "execution": "sequential",
        "system_policy": None,
        "repetitions": REPETITIONS,
        "cases": len(cases),
        "calls": len(results),
        "complete": complete,
        "response_stable_cases": sum(row["response_stable"] for row in stability),
        "oracle_stable_cases": sum(row["oracle_stable"] for row in stability),
        "oracle_passes_per_repetition": [
            sum(row["oracle_pass"] is True for row in results if row["repetition"] == repetition)
            for repetition in range(1, REPETITIONS + 1)
        ],
        "latency_ms": {
            "p50": percentile(latencies, 0.5),
            "p95": percentile(latencies, 0.95),
            "max": max(latencies, default=0),
        },
        "decision": decide(complete, len(cases), response_stable, oracle_stable),
        "manifests_sha256": {path.name: sha256(path) for path in MANIFESTS},
        "stability": stability,
        "results": results,
    }
    markdown = "\n".join([
        "# OpenMythos R28 Deterministic Repeatability",
        "",
        f"- decision: `{report['decision']['status']}`",
        f"- complete calls: `{len(results)}/{8 * REPETITIONS}`",
        f"- exact-response stable cases: `{report['response_stable_cases']}/{len(cases)}`",
        f"- oracle-outcome stable cases: `{report['oracle_stable_cases']}/{len(cases)}`",
        f"- oracle passes by repetition: `{report['oracle_passes_per_repetition']}`",
        f"- latency p50/p95/max ms: `{report['latency_ms']['p50']}/{report['latency_ms']['p95']}/{report['latency_ms']['max']}`",
        "",
    ])
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(markdown)
    print(markdown, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
