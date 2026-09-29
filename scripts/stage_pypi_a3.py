"""Verify and stage the four a3 release distributions against committed hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def stage(source: Path, output: Path) -> None:
    manifest = json.loads(Path(__file__).with_name("release-a3.json").read_text())
    expected_names = {
        f"{package}-0.1.0a3{suffix}"
        for package in ("narrative_contracts", "pytest_narrative_contracts")
        for suffix in ("-py3-none-any.whl", ".tar.gz")
    }
    if manifest["version"] != "0.1.0a3" or set(manifest["sha256"]) != expected_names:
        raise ValueError("Unexpected release manifest")
    if output.exists():
        raise FileExistsError("Output directory must be new")
    for name, expected in manifest["sha256"].items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Released artifact hash mismatch: {name}")
    output.mkdir(parents=True)
    for name in expected_names:
        shutil.copyfile(source / name, output / name)
    print("Verified and staged four original v0.1.0a3 release artifacts")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    stage(args.source, args.output)
