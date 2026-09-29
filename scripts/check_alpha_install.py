"""Exercise a3 APIs and pytest using installed distributions, never editable source."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from check_published_docs import ROOT, verify


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    verify(output, "0.1.0a3")
    text = (ROOT / "docs/policy-regression.md").read_text()
    blocks = re.findall(r"^```python\n(.*?)^```", text, re.MULTILINE | re.DOTALL)
    test = output / "test_policy_regression.py"
    test.write_text("\n\n".join(blocks))
    commands = [
        ["-m", "pytest", "-q", "-c", os.devnull, str(test), "--narrative-report=policy-audit.json"],
        [str(ROOT / "examples/audit_existing_validator.py"), "--output", str(output / "refund")],
        [str(ROOT / "examples/external_validators.py"), "--output", str(output / "integrations")],
    ]
    for index, command in enumerate(commands):
        result = subprocess.run(
            [sys.executable, "-I", *command], cwd=output, capture_output=True, text=True
        )
        (output / f"alpha-{index}.log").write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
    report = json.loads((output / "policy-audit.json").read_text())["reports"][0]
    assert report["library_version"] == "0.1.0a3"
    assert report["summary"]["counts"] == {"detected": 2, "preserved": 1}
    flags = report["summary"]["obligations"][0]
    assert flags["has_fault_tests"] and flags["has_controls"]
    assert not flags["has_known_gaps"] and not flags["has_incomplete_evidence"]
    (output / "alpha-summary.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "library_version": "0.1.0a3",
                "policy_regression": report["summary"],
                "checks": [
                    "installed paths and versions",
                    "consumer docs",
                    "CLI",
                    "pytest plugin",
                    "policy regression",
                    "refund demo",
                    "JSON Schema and Pydantic trials",
                ],
                "scope": "Installed artifact checks; not independent adoption or semantic accuracy.",
            },
            indent=2,
        )
        + "\n"
    )
    print("a3 installed-package regression, plugin, refund and third-party examples passed.")


if __name__ == "__main__":
    main()
