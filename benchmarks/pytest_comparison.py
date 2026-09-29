"""Execute ordinary pytest and MateProbe on the same refund-demo cases."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import validator_study as io

from narrative_contracts.validator_audit import audit_validator

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "examples/audit_existing_validator.py"
SUITE = ROOT / "examples/pytest_audit_comparison.py"


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location("refund_comparison_demo", DEMO)
    demo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(demo)
    junit = output.resolve() / "pytest.xml"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(SUITE.relative_to(ROOT)),
            "-q",
            "--tb=short",
            "--no-header",
            f"--junitxml={junit}",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env={**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
    )
    (output / "pytest-output.txt").write_text(result.stdout + result.stderr)
    if result.returncode not in (0, 1) or not junit.exists():
        raise RuntimeError("pytest infrastructure failure; output retained")
    ordinary = {}
    for node in ET.parse(junit).iter("testcase"):
        key = node.attrib["name"].split("[", 1)[1].removesuffix("]")
        if node.find("error") is not None or node.find("skipped") is not None or key in ordinary:
            raise ValueError("Unexpected pytest error, skip or duplicate")
        ordinary[key] = "failed" if node.find("failure") is not None else "passed"
    rows, reports, summary = [], {}, {}
    for name, validator in (
        ("before", demo.existing_validator),
        ("after", demo.corrected_validator),
    ):
        report = audit_validator(
            validator,
            demo.cases(),
            obligations=demo.OBLIGATIONS,
            validator_id=f"refund-demo/{name}/1",
        )
        reports[name] = report.to_dict()
        (output / f"{name}-audit.md").write_text(report.to_markdown())
        for case in report.cases:
            key = f"{name}::{case.id}"
            observed = ordinary.pop(key)
            expected = "passed" if case.outcome in ("detected", "preserved") else "failed"
            rows.append(
                {
                    "profile": name,
                    "id": case.id,
                    "relation": case.relation.value,
                    "expected_ids": list(case.expected),
                    "pytest": observed,
                    "audit": case.outcome,
                    "agree": expected == observed,
                }
            )
        summary[name] = {
            "pytest": dict(Counter(r["pytest"] for r in rows if r["profile"] == name)),
            "audit": report.summary(),
        }
    if ordinary:
        raise ValueError("pytest inventory has additional cases")
    summary = {
        "schema_version": 1,
        "paired_classifications": len(rows),
        "disagreements": sum(not r["agree"] for r in rows),
        "profiles": summary,
        "pytest_exit_code": result.returncode,
        "interpretation": "Same authored cases, same detections; no effort or usability claim.",
    }
    io.write_json(output / "comparisons.json", rows)
    io.write_json(output / "summary.json", summary)
    io.write_json(output / "audit-reports.json", reports)
    io.write_json(
        output / "manifest.json",
        {
            "python": platform.python_version(),
            "sources": {str(p.relative_to(ROOT)): io.sha(p) for p in (DEMO, SUITE, Path(__file__))},
            "outputs": {p.name: io.sha(p) for p in sorted(output.iterdir()) if p.is_file()},
        },
    )
    if summary["disagreements"]:
        raise AssertionError("Comparison mismatch retained")
    print(
        json.dumps(
            {
                "classifications": len(rows),
                "disagreements": summary["disagreements"],
                "pytest": {k: v["pytest"] for k, v in summary["profiles"].items()},
            },
            indent=2,
        )
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
