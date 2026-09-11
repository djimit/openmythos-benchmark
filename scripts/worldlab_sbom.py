#!/usr/bin/env python3
"""Emit the small WorldLab CycloneDX SBOM without adding a build dependency."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s]+)$")


def build(lock: Path) -> dict:
    components = []
    for line in lock.read_text().splitlines():
        match = PIN.match(line.strip())
        if match:
            name, version = match.groups()
            components.append({"type": "library", "name": name, "version": version,
                               "purl": f"pkg:pypi/{name.lower()}@{version}"})
    if not components:
        raise ValueError("dependency lock contains no exact pins")
    base = re.search(r"^FROM\s+([^\s@]+)@sha256:([a-f0-9]{64})$", (ROOT / "Dockerfile").read_text(), re.MULTILINE)
    if not base:
        raise ValueError("Docker base image must be digest pinned")
    image, digest = base.groups()
    components.append({"type": "container", "name": image, "version": f"sha256:{digest}",
                       "purl": f"pkg:oci/{image}@sha256:{digest}"})
    lock_hash = hashlib.sha256(lock.read_bytes()).hexdigest()
    return {
        "bomFormat": "CycloneDX", "specVersion": "1.5", "version": 1,
        "serialNumber": f"urn:uuid:{lock_hash[:8]}-{lock_hash[8:12]}-5{lock_hash[13:16]}-a{lock_hash[17:20]}-{lock_hash[20:32]}",
        "metadata": {
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "component": {"type": "application", "name": "openmythos-worldlab", "version": "0.1.0"},
            "properties": [{"name": "openmythos:dependency-lock-sha256", "value": lock_hash}],
        },
        "components": components,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", type=Path, default=ROOT / "requirements-lock.txt")
    parser.add_argument("--output", type=Path, default=ROOT / "analysis/worldlab/worldlab-sbom.cdx.json")
    args = parser.parse_args()
    document = build(args.lock)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {args.output} ({len(document['components'])} components)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
