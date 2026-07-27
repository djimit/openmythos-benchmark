#!/usr/bin/env python3
"""Fix the nl_governance_generator.py file."""

from pathlib import Path

f = Path(
    "/Users/dlandman/OpenMythos/openmythos-benchmark/scripts/nl_governance_generator.py"
)
lines = f.read_text().split("\n")

# Keep everything up to line 197 (the comment)
clean_lines = lines[:198]

# Add the main function
main_func = """
def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Dutch governance cases")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print(f"NL Governance Generator \\u2014 {len(NL_CASES)} cases")
    cats = set(c["category"] for c in NL_CASES)
    diff_min = min(c["difficulty"] for c in NL_CASES)
    diff_max = max(c["difficulty"] for c in NL_CASES)
    print(f"  Categories: {cats}")
    print(f"  Difficulty range: {diff_min}-{diff_max}")

    if args.dry_run:
        for case in NL_CASES:
            cid = case["id"]
            cat = case["category"]
            diff = case["difficulty"]
            prompt_preview = case["prompt"][:80]
            print(f"\\n  [{cid}] {cat} (L{diff})")
            print(f"    {prompt_preview}...")
        print(f"\\n[DRY RUN \\u2014 {len(NL_CASES)} cases, no files written]")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    content = "\\n".join(json.dumps(c, ensure_ascii=False) for c in NL_CASES) + "\\n"
    args.output.write_text(content)
    print(f"\\n  Wrote {args.output} ({len(NL_CASES)} cases)")
    print("\\nNext: review cases, add to corpus, run validation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""

clean_lines.append(main_func)

f.write_text("\n".join(clean_lines))
print(f"Fixed: {len(clean_lines)} lines written")
