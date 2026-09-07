#!/usr/bin/env python3
"""Run an explicitly enabled, tool-free local Ollama WorldLab campaign."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from worldlab.model_experiment import LocalModelCampaign


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--replications", type=int, default=30)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--artifact-mode", choices=["plain", "adversarial"], default="plain")
    parser.add_argument("--population", choices=["homogeneous", "heterogeneous"], default="heterogeneous")
    args = parser.parse_args()
    report = LocalModelCampaign(args.models, args.base_url, args.artifact_mode, args.population).run(args.output, args.replications)
    print(json.dumps({"status": report["status"], "invalid_response_rate": report["invalid_response_rate"]}))
    return 0 if report["status"] in {"SUPPORTED", "FALSIFIED", "UNDETERMINED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
