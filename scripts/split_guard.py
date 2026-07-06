#!/usr/bin/env python3
"""Fail when sealed OpenMythos audit case IDs leak into evolution artifacts."""

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DEFAULT_CORPUS = REPO_ROOT / "cases" / "corpus.jsonl"
DEFAULT_SCAN = [
    REPO_ROOT / "analysis" / "openmythos-advice-runs",
    REPO_ROOT / "analysis" / "openmythos-apex-runs",
    REPO_ROOT / "cases" / "drafts",
]
SPLITS = ("train_public", "dev_evolution", "sealed_audit")


def load_manifest(path: Path) -> dict[str, set[str]]:
    data = json.loads(path.read_text())
    raw = data.get("splits", data)
    if "cases" in data:
        raw = {split: [] for split in SPLITS}
        for row in data["cases"]:
            raw.setdefault(row["split"], []).append(row["case_id"])
    splits = {split: set(map(str, raw.get(split, []))) for split in SPLITS}
    unknown = set(raw) - set(SPLITS)
    if unknown:
        raise SystemExit(f"unknown split(s): {', '.join(sorted(unknown))}")
    overlap = split_overlap(splits)
    if overlap:
        raise SystemExit(f"case IDs appear in multiple splits: {', '.join(sorted(overlap))}")
    return splits


def split_overlap(splits: dict[str, set[str]]) -> set[str]:
    seen = {}
    overlap = set()
    for split, ids in splits.items():
        for case_id in ids:
            if case_id in seen and seen[case_id] != split:
                overlap.add(case_id)
            seen[case_id] = split
    return overlap


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def text_files(paths: list[Path]) -> list[Path]:
    files = []
    for path in paths:
        if path.is_file():
            files.append(path)
        elif path.exists():
            for child in path.rglob("*"):
                if child.is_file() and child.suffix.lower() in {".jsonl", ".json", ".md", ".txt", ".csv"}:
                    files.append(child)
    return sorted(files)


def scan(paths: list[Path], sealed_ids: set[str]) -> tuple[list[dict], int]:
    violations = []
    for path in text_files(paths):
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        for case_id in sorted(sealed_ids):
            if case_id in text:
                violations.append({"case_id": case_id, "path": str(path)})
    return violations, len(text_files(paths))


def summarize(
    manifest: Path,
    splits: dict[str, set[str]],
    paths: list[Path],
    violations: list[dict],
    scanned_files: int,
    corpus: Path | None = None,
) -> dict:
    report = {
        "passed": not violations,
        "manifest": {"path": str(manifest), "sha256": sha256(manifest)},
        "split_counts": {split: len(ids) for split, ids in splits.items()},
        "scanned_paths": [str(path) for path in paths],
        "scanned_files": scanned_files,
        "violations": violations,
    }
    if corpus and corpus.exists():
        report["corpus"] = {"path": str(corpus), "sha256": sha256(corpus)}
    return report


def print_summary(report: dict) -> None:
    counts = " ".join(f"{split}={count}" for split, count in report["split_counts"].items())
    print(f"splits: {counts}")
    print(f"scanned_paths={len(report['scanned_paths'])} scanned_files={report['scanned_files']}")
    if report["violations"]:
        print("\nviolations:")
        for row in report["violations"]:
            print(f"  {row['case_id']} {row['path']}")
        print("\nFAILED - sealed split guard failed")
    else:
        print("\nOK - sealed split guard passed")


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def demo() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        manifest = root / "split.json"
        manifest.write_text(json.dumps({"splits": {"sealed_audit": ["sealed-001"], "dev_evolution": [], "train_public": []}}))
        clean = root / "clean.md"
        bad = root / "bad.md"
        clean.write_text("no sealed IDs here")
        bad.write_text("leak sealed-001")
        splits = load_manifest(manifest)
        bad_report = summarize(manifest, splits, [bad], *scan([bad], splits["sealed_audit"]))
        clean_report = summarize(manifest, splits, [clean], *scan([clean], splits["sealed_audit"]))
        assert not bad_report["passed"], bad_report
        assert clean_report["passed"], clean_report
    print("demo OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--scan", nargs="*", type=Path, default=DEFAULT_SCAN)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo:
        return demo()
    if not args.manifest:
        parser.error("--manifest is required unless --demo")

    splits = load_manifest(args.manifest)
    violations, scanned_files = scan(args.scan, splits["sealed_audit"])
    report = summarize(args.manifest, splits, args.scan, violations, scanned_files, args.corpus)
    print_summary(report)
    if args.summary:
        write_json(args.summary, report)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
