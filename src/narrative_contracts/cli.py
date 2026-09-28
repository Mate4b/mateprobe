from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .engine import evaluate
from .serialization import load_bundle


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate a deterministic narrative contract bundle"
    )
    parser.add_argument(
        "bundle", type=Path, help="JSON document, context and contract configuration"
    )
    parser.add_argument("--output", type=Path, help="Write the JSON report to this file")
    args = parser.parse_args()
    try:
        document, context, rules, policy = load_bundle(json.loads(args.bundle.read_text("utf-8")))
        report = evaluate(document, context, rules, policy)
        output = json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(output, encoding="utf-8")
        else:
            print(output, end="")
        return 0 if report.accepted else 1
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(f"Invalid contract bundle: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
