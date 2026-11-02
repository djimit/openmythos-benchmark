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
    parser.add_argument("--design", choices=["bundled", "factorial"], default="bundled")
    parser.add_argument("--calibrate-only", action="store_true")
    parser.add_argument("--calibration-report", type=Path)
    parser.add_argument("--calibration-replications", type=int, default=5)
    args = parser.parse_args()
    campaign = LocalModelCampaign(args.models, args.base_url, args.artifact_mode, args.population)
    if args.calibrate_only:
        report = campaign.calibrate(args.output, args.calibration_replications)
        print(json.dumps({"state": report["state"], "invalid_response_rate": report["invalid_response_rate"]}))
        return 0
    calibration = json.loads(args.calibration_report.read_text()) if args.calibration_report else None
    report = campaign.run(args.output, args.replications, args.design, calibration)
    print(json.dumps({"status": report["status"], "invalid_response_rate": report["invalid_response_rate"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
