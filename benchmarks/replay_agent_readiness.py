"""Replay the frozen a3 consumer and reviewer checks, without rerunning web searches."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "benchmarks/agent-readiness/v2"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="A new evidence directory")
    args = parser.parse_args()
    manifest = json.loads((FROZEN / "manifest.json").read_text())
    for name, expected in manifest["artifact_sha256"].items():
        if hashlib.sha256((FROZEN / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"Frozen evidence changed: {name}")
    probe = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import json, importlib.metadata as m, narrative_contracts as n; "
            "print(json.dumps({'module': n.__file__, 'versions': "
            "{p:m.version(p) for p in ['narrative-contracts','pytest-narrative-contracts','pytest']}}))",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    installed = json.loads(probe.stdout)
    if Path(installed["module"]).resolve().is_relative_to(ROOT):
        raise RuntimeError("Use an isolated installed-package environment, not this checkout")
    for name in ("narrative-contracts", "pytest-narrative-contracts"):
        if installed["versions"][name] != "0.1.0a3":
            raise RuntimeError(f"This frozen trial requires published a3: {name}")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    for name in ("allocation_audit.py", "test_allocation_audit.py"):
        shutil.copyfile(FROZEN / "integration/submission" / (name + ".txt"), output / name)
    shutil.copyfile(FROZEN / "integration/reviewer_checks.py.txt", output / "test_reviewer.py")
    (output / "pytest.ini").write_text("[pytest]\naddopts = -ra\n")
    # Only add the copied consumer directory. The library comes from site-packages.
    bootstrap = (
        "import sys, pytest; from pathlib import Path; "
        "root=Path(sys.argv[1]); sys.path.insert(0,str(root)); "
        "raise SystemExit(pytest.main(['-q','-c',str(root/'pytest.ini'),"
        "'--narrative-report=contract-results.json','--junitxml=tests.xml',"
        "str(root/'test_allocation_audit.py'),str(root/'test_reviewer.py')]))"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", bootstrap, str(output)],
        cwd=output,
        capture_output=True,
        text=True,
    )
    (output / "stdout.txt").write_text(result.stdout + result.stderr)
    summary = {
        "status": "passed" if result.returncode == 0 else "failed",
        "exit_code": result.returncode,
        "versions": installed["versions"],
        "python": sys.version.split()[0],
        "scope": "Frozen a3 integration replay; not a new agent run or search-discovery trial.",
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(result.stdout + result.stderr)
    print(json.dumps(summary, indent=2))
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
