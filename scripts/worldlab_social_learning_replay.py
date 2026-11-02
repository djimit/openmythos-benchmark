#!/usr/bin/env python3
"""Replay a DjimitFlo social-learning campaign without production access."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from worldlab.social_learning import replay_campaign


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--traces", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    result = replay_campaign(json.loads(args.input.read_text()), args.source_commit, args.traces)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"campaign_id": result["campaign_id"], "status": result["status"], "trajectories": result["trajectories"], "causal_claim_supported": False, "evidence_hash": result["evidence_hash"]}))
    return 0 if result["status"] in {"PASS", "UNDETERMINED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
