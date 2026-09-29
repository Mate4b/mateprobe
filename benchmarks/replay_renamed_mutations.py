"""Replay the frozen generator unchanged against MateProbe in an isolated subprocess.

Only its historical import names are bound to the renamed library. Frozen source,
corpus checks, labels and rule configuration are not rewritten or bypassed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "benchmarks/real-mutation-results/prepared"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = (FROZEN / "prepared.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != (FROZEN / "SHA256SUMS").read_text().split()[0]:
        raise ValueError("Prepared corpus hash mismatch")
    payload = json.loads(raw)
    with tempfile.TemporaryDirectory(prefix="mateprobe-frozen-replay-") as directory:
        root = Path(directory)
        scripts = root / "benchmarks"
        scripts.mkdir()
        for source, target, key in (
            ("generator-source.py.txt", "real_mutations.py", "generator_sha256"),
            ("adapter-source.py.txt", "natural.py", "adapter_sha256"),
        ):
            content = (FROZEN / source).read_bytes()
            if hashlib.sha256(content).hexdigest() != payload[key]:
                raise ValueError(f"Frozen source hash mismatch: {source}")
            (scripts / target).write_bytes(content)
        bootstrap = """
import runpy, sys
import mateprobe, mateprobe.model, mateprobe.mutations
# Compatibility is confined to this replay process, not installed as public aliases.
sys.modules['narrative_contracts'] = mateprobe
sys.modules['narrative_contracts.model'] = mateprobe.model
sys.modules['narrative_contracts.mutations'] = mateprobe.mutations
script, prepared, output = sys.argv[1:]
sys.argv = [script, 'evaluate', '--prepared', prepared, '--output', output]
runpy.run_path(script, run_name='__main__')
"""
        subprocess.run(
            [
                sys.executable,
                "-I",
                "-c",
                bootstrap,
                str(scripts / "real_mutations.py"),
                str(FROZEN),
                str(args.output.resolve()),
            ],
            cwd=root,
            check=True,
        )


if __name__ == "__main__":
    main()
