"""Stage the four previously released a2 distributions, verifying pinned byte hashes."""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

HASHES = {
    "narrative_contracts-0.1.0a2-py3-none-any.whl": "2f12ba226df94d99eaffb6f07f5cf5f278e951ec7f045b45caddcb6aefa3c9c3",
    "narrative_contracts-0.1.0a2.tar.gz": "002377243a85bfd3ca1039c0e731a7427f9a82fbdeb6ce9c38dacea6a91e7a9c",
    "pytest_narrative_contracts-0.1.0a2-py3-none-any.whl": "424a08ac11e828036b45697c435b954845508056a298c54c92f6f33542be91cf",
    "pytest_narrative_contracts-0.1.0a2.tar.gz": "8f0a380f77c5c2bb0df4b56cd599f3701ee70a1234b5601b97081939ec6a540c",
}


def stage(source: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError("Output directory must be new")
    for name, expected in HASHES.items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Released artifact hash mismatch: {name}")
    output.mkdir(parents=True)
    for name in HASHES:
        shutil.copyfile(source / name, output / name)
    print("Verified and staged four original v0.1.0a2 release artifacts")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    stage(args.source, args.output)
