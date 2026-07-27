#!/usr/bin/env python3
"""Spec Compliance Gate — DDD artifact completeness verification.

7th gate in the OpenMythos model promotion pipeline.
Verifies that a project's /specs folder contains all required DDD artifacts
per Constitution v1.2.0 Article VI.

Usage:
    python3 spec_compliance_gate.py --specs-dir /path/to/project/specs/
    python3 spec_compliance_gate.py --specs-dir /path/to/project/specs/ --change-type greenfield
    python3 spec_compliance_gate.py --demo
"""

import argparse
import json
import re
import sys
from pathlib import Path


# Required artifacts per change type (Constitution v1.2.0 Article VI.5)
ARTIFACT_REQUIREMENTS = {
    "greenfield": {
        "required": ["domain-terms.md", "bc-{name}.md", "requirements.md"],
        "conditional": ["aggregate-{name}.md"],
        "optional": ["context-map.md", "events.yaml", "subdomain-classification.md"],
    },
    "brownfield": {
        "required": ["bc-{name}.md"],
        "conditional": ["aggregate-{name}.md", "acl-{system}.md"],
        "optional": ["domain-terms.md", "context-map.md"],
    },
    "external": {
        "required": ["acl-{external}.md", "events.yaml"],
        "conditional": [],
        "optional": ["context-map.md", "domain-terms.md"],
    },
    "bugfix": {
        "required": [],
        "conditional": [],
        "optional": ["domain-terms.md"],
    },
}


def check_artifact_exists(specs_dir, artifact_pattern):
    """Check if an artifact exists, supporting {name} wildcards."""
    if "{name}" in artifact_pattern or "{external}" in artifact_pattern:
        glob_pattern = artifact_pattern.replace("{name}", "*").replace("{external}", "*")
        matches = list(specs_dir.rglob(glob_pattern))
        return len(matches) > 0
    return (specs_dir / artifact_pattern).exists()


def check_ul_completeness(specs_dir):
    """Check that domain-terms.md has required fields."""
    results = {"present": False, "terms": 0, "aliases_defined": 0, "issues": []}

    for glossary_file in specs_dir.rglob("domain-terms.md"):
        content = glossary_file.read_text()
        results["present"] = True
        terms = re.findall(r"^## Term:", content, re.MULTILINE)
        results["terms"] = len(terms)
        aliases = re.findall(r"Aliases to AVOID:", content)
        results["aliases_defined"] = len(aliases)

        if len(terms) == 0:
            results["issues"].append(f"{glossary_file}: no terms defined")
        if len(aliases) == 0:
            results["issues"].append(f"{glossary_file}: no Aliases to AVOID sections")

    return results


def check_aggregate_invariants(specs_dir):
    """Check that aggregate specs have EARS invariants."""
    results = {"present": False, "count": 0, "total_invariants": 0, "issues": []}

    for agg_file in specs_dir.rglob("aggregate-*.md"):
        results["present"] = True
        results["count"] += 1
        content = agg_file.read_text()
        invariants = re.findall(r"INV-[0-9]{3}", content)
        results["total_invariants"] += len(invariants)

        if len(invariants) < 1:
            results["issues"].append(f"{agg_file}: no INV-### identifiers")

        if "WHEN" not in content or "SHALL" not in content:
            results["issues"].append(f"{agg_file}: missing EARS keywords (WHEN/THEN/SHALL)")

    return results


def check_acl_completeness(specs_dir):
    """Check that ACL specs have forbidden concepts."""
    results = {"present": False, "count": 0, "total_forbidden": 0, "issues": []}

    for acl_file in specs_dir.rglob("acl-*.md"):
        results["present"] = True
        results["count"] += 1
        content = acl_file.read_text()

        if "Forbidden Concepts" not in content:
            results["issues"].append(f"{acl_file}: missing Forbidden Concepts section")

    return results


def run_gate(specs_dir, change_type="greenfield", thresholds=None):
    """Run spec compliance gate. Returns (passed, details)."""
    thresholds = thresholds or {}
    min_terms = thresholds.get("min_terms", 3)

    details = {
        "gate": "spec_compliance",
        "change_type": change_type,
        "specs_dir": str(specs_dir),
        "artifacts": {},
        "ul": {},
        "aggregates": {},
        "acls": {},
        "issues": [],
        "passed": False,
    }

    if not specs_dir.exists():
        details["issues"].append(f"specs directory not found: {specs_dir}")
        return False, details

    requirements = ARTIFACT_REQUIREMENTS.get(change_type, ARTIFACT_REQUIREMENTS["greenfield"])

    for artifact in requirements["required"]:
        found = check_artifact_exists(specs_dir, artifact)
        details["artifacts"][artifact] = "FOUND" if found else "MISSING"
        if not found:
            details["issues"].append(f"Required artifact missing: {artifact}")

    for artifact in requirements["conditional"]:
        found = check_artifact_exists(specs_dir, artifact)
        details["artifacts"][artifact] = "FOUND" if found else "NOT_FOUND (conditional)"

    ul_result = check_ul_completeness(specs_dir)
    details["ul"] = ul_result
    if ul_result["present"] and ul_result["terms"] < min_terms:
        details["issues"].append(
            f"domain-terms.md has {ul_result['terms']} terms, need >= {min_terms}"
        )
    details["issues"].extend(ul_result.get("issues", []))

    agg_result = check_aggregate_invariants(specs_dir)
    details["aggregates"] = agg_result
    details["issues"].extend(agg_result.get("issues", []))

    acl_result = check_acl_completeness(specs_dir)
    details["acls"] = acl_result
    details["issues"].extend(acl_result.get("issues", []))

    required_missing = any(v == "MISSING" for v in details["artifacts"].values())
    details["passed"] = not required_missing and len(details["issues"]) == 0
    return details["passed"], details


def render_report(details):
    """Format gate results as markdown."""
    status = "PASS" if details["passed"] else "FAIL"
    lines = [
        "# Spec Compliance Gate Report",
        "",
        f"**Gate: SPEC_COMPLIANCE — {status}**",
        f"**Change type: {details['change_type']}**",
        f"**Specs dir: {details['specs_dir']}**",
        "",
        "## Artifacts",
        "",
        "| artifact | status |",
        "|----------|--------|",
    ]
    for artifact, state in details["artifacts"].items():
        lines.append(f"| {artifact} | {state} |")

    lines.extend([
        "",
        "## Ubiquitous Language",
        "",
        f"- Terms: {details['ul'].get('terms', 0)}",
        f"- Aliases defined: {details['ul'].get('aliases_defined', 0)}",
    ])

    if details["aggregates"].get("present"):
        lines.extend([
            "",
            "## Aggregate Specs",
            "",
            f"- Count: {details['aggregates']['count']}",
            f"- Total invariants: {details['aggregates']['total_invariants']}",
        ])

    if details["acls"].get("present"):
        lines.extend([
            "",
            "## ACL Specs",
            "",
            f"- Count: {details['acls']['count']}",
        ])

    if details["issues"]:
        lines.extend(["", "## Issues", ""])
        for issue in details["issues"]:
            lines.append(f"- {issue}")

    lines.append("")
    return "\n".join(lines)


def demo():
    """Self-check with mock results."""
    details = {
        "gate": "spec_compliance",
        "change_type": "greenfield",
        "specs_dir": "/mock/specs",
        "artifacts": {
            "domain-terms.md": "FOUND",
            "bc-{name}.md": "FOUND",
            "aggregate-{name}.md": "FOUND",
            "requirements.md": "FOUND",
        },
        "ul": {"present": True, "terms": 8, "aliases_defined": 8},
        "aggregates": {"present": True, "count": 2, "total_invariants": 12},
        "acls": {"present": False, "count": 0, "total_forbidden": 0},
        "issues": [],
        "passed": True,
    }
    report = render_report(details)
    assert "PASS" in report

    details["passed"] = False
    details["issues"] = ["Required artifact missing: domain-terms.md"]
    details["artifacts"]["domain-terms.md"] = "MISSING"
    report_fail = render_report(details)
    assert "FAIL" in report_fail

    print("spec_compliance_gate demo OK")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--specs-dir", type=Path, help="Path to /specs folder")
    parser.add_argument(
        "--change-type",
        choices=["greenfield", "brownfield", "external", "bugfix"],
        default="greenfield",
    )
    parser.add_argument("--min-terms", type=int, default=3)
    parser.add_argument("--output", type=Path, help="Write report to file")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo:
        return demo()

    if not args.specs_dir:
        parser.error("--specs-dir required (or use --demo)")

    thresholds = {"min_terms": args.min_terms}
    passed, details = run_gate(args.specs_dir, args.change_type, thresholds)
    report = render_report(details)
    print(report)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report + "\n")

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
