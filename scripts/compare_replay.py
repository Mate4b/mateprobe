"""Compare frozen pilot reports, permitting only the declared package-version change."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


def compare(
    frozen: list[dict],
    replay: list[dict],
    old_version: str,
    new_version: str,
    report_path: tuple[str, ...] = ("report",),
) -> None:
    def report(row: dict) -> dict | None:
        value = row
        for key in report_path:
            value = value.get(key)
            if value is None:
                return None
        return value

    normalized = copy.deepcopy(replay)
    for rows, expected in ((frozen, old_version), (normalized, new_version)):
        for row in rows:
            if (value := report(row)) is not None:
                if value["library_version"] != expected:
                    raise ValueError("Unexpected report library version")
    for row in normalized:
        if (value := report(row)) is not None:
            value["library_version"] = old_version
    if frozen != normalized:
        raise ValueError("Replay changed beyond the declared library version")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frozen", type=Path)
    parser.add_argument("replay", type=Path)
    parser.add_argument("--old-version", required=True)
    parser.add_argument("--new-version", required=True)
    parser.add_argument("--report-path", choices=("report", "result.report"), default="report")
    args = parser.parse_args()
    compare(
        json.loads(args.frozen.read_text()),
        json.loads(args.replay.read_text()),
        args.old_version,
        args.new_version,
        tuple(args.report_path.split(".")),
    )
    print("Replay matches; only the declared library version may differ.")
