"""Replay frozen consumer code and maintainer checks using published PyPI a2."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "benchmarks/agent-adoption/v1"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New evidence directory")
    args = parser.parse_args()
    manifest = json.loads((FROZEN / "manifest.json").read_text())
    for name, expected in manifest["artifact_sha256"].items():
        if hashlib.sha256((FROZEN / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"Frozen artifact changed: {name}")
    probe = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import narrative_contracts as n; print(n.__file__)",
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    if Path(probe.stdout.strip()).resolve().is_relative_to(ROOT):
        raise RuntimeError("Use an isolated published-package environment, not this checkout")
    versions = {
        name: importlib.metadata.version(name)
        for name in ("narrative-contracts", "pytest-narrative-contracts", "pytest", "pydantic")
    }
    for name in ("narrative-contracts", "pytest-narrative-contracts"):
        if versions[name] != "0.1.0a2":
            raise RuntimeError(f"Replay needs published 0.1.0a2: {name}")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    for name in ("shipping_contract.py", "test_shipping_contract.py", "generate_report.py"):
        shutil.copyfile(FROZEN / "submission" / (name + ".txt"), output / name)
    shutil.copyfile(FROZEN / "reviewer_checks.py.txt", output / "test_reviewer.py")
    # Keep pytest configuration local and independent of the repository.
    (output / "pytest.ini").write_text("[pytest]\naddopts = -ra\n")
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "pytest",
            "-q",
            "-c",
            str(output / "pytest.ini"),
            "--narrative-report=contract-results.json",
            "--junitxml=tests.xml",
            str(output / "test_shipping_contract.py"),
            str(output / "test_reviewer.py"),
        ],
        cwd=output,
        capture_output=True,
        text=True,
    )
    (output / "stdout.txt").write_text(result.stdout + result.stderr)
    summary = {
        "status": "passed" if result.returncode == 0 else "failed",
        "exit_code": result.returncode,
        "versions": versions,
        "docs_revision": manifest["docs_revision"],
        "python": sys.version.split()[0],
        "scope": "Replay of frozen integration and reviewer checks, not a new agent trial.",
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(result.stdout + result.stderr)
    print(json.dumps(summary, indent=2))
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
