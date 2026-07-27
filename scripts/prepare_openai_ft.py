#!/usr/bin/env python3
"""Convert OpenMythos SFT data to OpenAI fine-tuning format.

OpenAI format (chat):
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}

Usage:
    python3 scripts/prepare_openai_ft.py \
      --input analysis/openmythos-apex-runs/datasets/apex-r10-sft-gemma4.jsonl \
      --output analysis/openmythos-apex-runs/datasets/r12-openai-ft.jsonl
"""

import argparse
import json
from pathlib import Path


def convert_to_openai_format(input_path: Path, output_path: Path) -> int:
    """Convert instruction/output to OpenAI chat format."""
    count = 0
    with input_path.open() as fin, output_path.open("w") as fout:
        for line in fin:
            if not line.strip():
                continue
            entry = json.loads(line)
            # Support both formats
            if "instruction" in entry and "output" in entry:
                messages = [
                    {"role": "user", "content": entry["instruction"]},
                    {"role": "assistant", "content": entry["output"]},
                ]
            elif "messages" in entry:
                messages = entry["messages"]
            else:
                continue

            fout.write(json.dumps({"messages": messages}) + "\n")
            count += 1

    return count


def validate_format(path: Path) -> list[str]:
    """Validate OpenAI fine-tuning format."""
    errors = []
    with path.open() as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            entry = json.loads(line)
            if "messages" not in entry:
                errors.append(f"Line {i}: missing 'messages'")
                continue
            msgs = entry["messages"]
            if len(msgs) < 2:
                errors.append(f"Line {i}: need at least 2 messages")
            if msgs[0].get("role") != "user":
                errors.append(f"Line {i}: first message must be 'user'")
            if msgs[-1].get("role") != "assistant":
                errors.append(f"Line {i}: last message must be 'assistant'")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    if args.validate_only:
        errors = validate_format(args.input)
        if errors:
            for e in errors:
                print(f"ERROR: {e}")
            return 1
        print(f"Format valid: {args.input}")
        return 0

    count = convert_to_openai_format(args.input, args.output)
    print(f"Converted {count} entries to {args.output}")

    errors = validate_format(args.output)
    if errors:
        for e in errors:
            print(f"WARNING: {e}")
        return 1

    print("Validation passed")
    return 0


if __name__ == "__main__":
    main()
