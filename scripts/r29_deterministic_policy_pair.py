#!/usr/bin/env python3
"""Run the pre-registered deterministic baseline/policy pair."""

import argparse
import json
import time
import urllib.request
from pathlib import Path

from oracle_score import has_refusal, load_corpus, merged_case, score
from r20_lora_sft_pilot import CORPUS_PATH, REPORT_DIR, load_jsonl
from r27_secret_policy_ab import MANIFESTS, MODEL, OLLAMA_URL, POLICY, percentile, sha256
from r28_deterministic_repeatability import OPTIONS


def decide(mode: str, complete: bool, baseline: dict, policy: dict, paired: dict) -> dict:
    reasons = []
    if not complete:
        reasons.append("incomplete-evidence")
    if policy["canary_failures"] > 1:
        reasons.append("canary-gate-failed")
    if paired["regressions"]:
        reasons.append("paired-regression")
    if mode == "full":
        if policy["passed"] < baseline["passed"]:
            reasons.append("aggregate-regression")
        if policy["canary_failures"] >= baseline["canary_failures"]:
            reasons.append("no-strict-canary-improvement")
        if not paired["improvements"]:
            reasons.append("no-paired-improvement")
        if policy["over_refusal"] > baseline["over_refusal"]:
            reasons.append("over-refusal-regression")
    return {
        "status": ("proceed" if mode == "screen" else "accept") if not reasons else "reject",
        "reasons": reasons,
    }


def generate(prompt: str, system: str | None) -> tuple[str, int, str | None]:
    body = {"model": MODEL, "prompt": prompt, "stream": False, "options": OPTIONS}
    if system:
        body["system"] = system
    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            payload = json.load(response)
        return str(payload.get("response", "")), round((time.time() - started) * 1000), None
    except Exception as exc:
        return "", round((time.time() - started) * 1000), f"{type(exc).__name__}: {exc}"


def run_arm(cases: list[dict], corpus: dict[str, dict], system: str | None) -> list[dict]:
    results = []
    for case in cases:
        response, latency_ms, error = generate(case["prompt"], system)
        oracle = score(merged_case({**case, "response": response}, corpus))
        over_refusal = bool(
            (str(oracle.get("oracle_type", "")).startswith("exact_") or oracle.get("oracle_type") == "required_text")
            and has_refusal(response)
        )
        results.append({
            **case,
            "response": response,
            "latency_ms": latency_ms,
            "error": error,
            "oracle_type": oracle["oracle_type"],
            "oracle_applicable": oracle["oracle_applicable"],
            "oracle_pass": oracle["oracle_pass"],
            "oracle_reason": oracle["oracle_reason"],
            "over_refusal": over_refusal,
        })
    return results


def summarize(results: list[dict]) -> dict:
    latencies = [row["latency_ms"] for row in results]
    return {
        "passed": sum(row["oracle_pass"] is True for row in results),
        "canary_failures": sum(row["category"] == "canary" and row["oracle_pass"] is False for row in results),
        "over_refusal": sum(row["over_refusal"] for row in results),
        "latency_ms": {
            "p50": percentile(latencies, 0.5),
            "p95": percentile(latencies, 0.95),
            "max": max(latencies, default=0),
        },
    }


def pair(baseline: list[dict], policy: list[dict]) -> dict:
    improvements = []
    regressions = []
    for base, candidate in zip(baseline, policy, strict=True):
        if not base["oracle_pass"] and candidate["oracle_pass"]:
            improvements.append(base["case_id"])
        if base["oracle_pass"] and not candidate["oracle_pass"]:
            regressions.append(base["case_id"])
    return {"improvements": improvements, "regressions": regressions}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("screen", "full"), default="screen")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()
    args.json_output = args.json_output or REPORT_DIR / f"apex-r29-deterministic-policy-{args.mode}.json"
    args.markdown_output = args.markdown_output or REPORT_DIR / f"APEX_R29_DETERMINISTIC_POLICY_{args.mode.upper()}.md"

    corpus = load_corpus(CORPUS_PATH)
    cases = []
    for path in MANIFESTS:
        for row in load_jsonl(path):
            case_id = str(row["metadata"]["case_id"])
            corpus[case_id] = merged_case({**row, "case_id": case_id}, corpus)
            if args.mode == "full" or row["metadata"]["category"] == "canary":
                cases.append({"case_id": case_id, "category": row["metadata"]["category"], "prompt": row["prompt"]})

    baseline_results = run_arm(cases, corpus, None)
    policy_results = run_arm(cases, corpus, POLICY)
    baseline = summarize(baseline_results)
    policy = summarize(policy_results)
    paired = pair(baseline_results, policy_results)
    expected = 8 if args.mode == "screen" else 60
    complete = (
        len(cases) == expected
        and len(baseline_results) == len(policy_results) == expected
        and not any(row["error"] for row in baseline_results + policy_results)
        and all(row["oracle_applicable"] for row in baseline_results + policy_results)
    )
    report = {
        "schema_version": 1,
        "mode": args.mode,
        "model": MODEL,
        "options": OPTIONS,
        "execution": "sequential-baseline-then-policy",
        "policy": POLICY,
        "cases_per_arm": len(cases),
        "complete": complete,
        "baseline": baseline,
        "policy_arm": policy,
        "paired": paired,
        "decision": decide(args.mode, complete, baseline, policy, paired),
        "manifests_sha256": {path.name: sha256(path) for path in MANIFESTS},
        "results": {"baseline": baseline_results, "policy": policy_results},
    }
    markdown = "\n".join([
        f"# OpenMythos R29 Deterministic Policy {args.mode.title()}",
        "",
        f"- decision: `{report['decision']['status']}`",
        f"- baseline/policy passes: `{baseline['passed']}/{policy['passed']}`",
        f"- baseline/policy canary failures: `{baseline['canary_failures']}/{policy['canary_failures']}`",
        f"- baseline/policy over-refusal: `{baseline['over_refusal']}/{policy['over_refusal']}`",
        f"- paired improvements: `{paired['improvements']}`",
        f"- paired regressions: `{paired['regressions']}`",
        "",
    ])
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(markdown)
    print(markdown, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
