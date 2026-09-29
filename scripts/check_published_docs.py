"""Run consumer documentation against installed PyPI a2, never editable source."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ("docs/quickstart.md", "docs/agent-guide.md")
EXAMPLES = (
    "examples/five_minute_demo.py",
    "examples/mutation_audit.py",
    "examples/pydantic_reply.py",
)


def verify(output: Path) -> None:
    def run(label: str, *args: str) -> str:
        result = subprocess.run(
            [sys.executable, "-I", *args], cwd=output, capture_output=True, text=True
        )
        (output / f"{label}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"{label} failed:\n{result.stdout}{result.stderr}")
        return result.stdout

    installation = json.loads(
        run(
            "installation",
            "-c",
            "import json, importlib.metadata as m, narrative_contracts as n; "
            "print(json.dumps({'module': n.__file__, 'versions': "
            "{p: m.version(p) for p in "
            "['narrative-contracts', 'pytest-narrative-contracts', 'pytest', 'pydantic']}}))",
        )
    )
    module_path = Path(installation["module"]).resolve()
    if module_path.is_relative_to(ROOT) or "site-packages" not in module_path.parts:
        raise RuntimeError(f"Expected an isolated installed package, got {module_path}")
    for package in ("narrative-contracts", "pytest-narrative-contracts"):
        if installation["versions"][package] != "0.1.0a2":
            raise RuntimeError(f"Wrong published version of {package}")

    sources = {}
    for name in DOCS:
        path = ROOT / name
        text = path.read_text(encoding="utf-8")
        blocks = re.findall(r"^```python\n(.*?)^```", text, re.MULTILINE | re.DOTALL)
        if not blocks:
            raise RuntimeError(f"No executable Python blocks in {name}")
        (output / f"test_{path.stem.replace('-', '_')}.py").write_text("\n\n".join(blocks))
        sources[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    run(
        "pytest",
        "-m",
        "pytest",
        "-q",
        "-c",
        os.devnull,
        "--narrative-report=contract-results.json",
        str(output),
    )
    records = json.loads((output / "contract-results.json").read_text())["reports"]
    if len(records) != 4 or any(record["library_version"] != "0.1.0a2" for record in records):
        raise RuntimeError("Expected four recorded evaluations from published a2")

    for name in EXAMPLES:
        path = ROOT / name
        run(path.stem, str(path))
        sources[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    run(
        "cli",
        "-m",
        "narrative_contracts.cli",
        str(ROOT / "examples/valid.json"),
        "--output",
        str(output / "cli-report.json"),
    )
    if not (output / "cli-report.json").is_file():
        raise RuntimeError("CLI did not write its report")
    result = {
        "status": "passed",
        "versions": installation["versions"],
        "python": sys.version.split()[0],
        "markdown_tests": 2,
        "recorded_evaluations": len(records),
        "examples": list(EXAMPLES),
        "cli": "passed",
        "source_sha256": sources,
        "scope": "Consumer example compatibility; not agent discovery or semantic accuracy.",
    }
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="New directory for retained evidence")
    args = parser.parse_args()
    if args.output:
        args.output.mkdir(parents=True, exist_ok=False)
        verify(args.output.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix="narrative-published-docs-") as directory:
            verify(Path(directory))


if __name__ == "__main__":
    main()
