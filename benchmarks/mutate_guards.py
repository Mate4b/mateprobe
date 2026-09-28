"""A small, explicit source-mutation experiment on disposable copies.

This complements output mutations. It is NOT exhaustive mutation analysis.
Only pytest assertion failures (exit 1) count as kills; collection errors,
timeouts and invalid replacements are reported separately.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUTANTS = (
    (
        "coerce_fact_types",
        "model.py",
        "return canonical(left) == canonical(right)",
        "return left == right",
    ),
    (
        "ignore_branch_scope",
        "rules.py",
        "facts = context.states.get(surface.state_ref)",
        "facts = next(iter(context.states.values()), None)",
    ),
    ("invert_state_change", "rules.py", "if not same(a[k], b[k])", "if same(a[k], b[k])"),
    ("remove_diversity_floor", "rules.py", " and len(set(words)) >= self.minimum_unique", ""),
    (
        "restore_length_escape",
        "rules.py",
        "reject = overlap > self.overlap_threshold and novel < self.minimum_novel_tokens",
        "reject = overlap > self.overlap_threshold and novel < self.minimum_novel_tokens "
        "and len(document.surface(self.target).text) < 90",
    ),
    (
        "remove_unicode_case_normalization",
        "text.py",
        'text = unicodedata.normalize("NFKC", text).casefold()',
        "text = text",
    ),
    ("ignore_detection_scope", "mutations.py", "and c.scope == self.scope", "and True"),
    ("swallow_rule_error", "engine.py", "Status.ERROR,", "Status.SATISFIED,"),
)


def run_tests(src):
    env = {
        **os.environ,
        "PYTHONPATH": str(src),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
    }
    return subprocess.run(
        [sys.executable, "-m", "pytest", str(ROOT / "tests"), "-q", "-p", "no:cacheprovider"],
        cwd=src.parent,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=ROOT / "benchmarks/results/source-mutations.json"
    )
    args = parser.parse_args()
    baseline = run_tests(ROOT / "src")
    if baseline.returncode:
        raise SystemExit("Baseline tests must pass before source mutation:\n" + baseline.stdout)
    results = []
    for name, filename, old, new in MUTANTS:
        with tempfile.TemporaryDirectory(prefix="narrative-mutant-") as directory:
            src = Path(directory) / "src"
            shutil.copytree(ROOT / "src", src, ignore=shutil.ignore_patterns("__pycache__"))
            path = src / "narrative_contracts" / filename
            original = path.read_text()
            if original.count(old) != 1:
                results.append(
                    {"id": name, "outcome": "invalid", "reason": "replacement_not_unique"}
                )
                continue
            path.write_text(original.replace(old, new))
            try:
                completed = run_tests(src)
                outcome = {0: "survived", 1: "killed"}.get(completed.returncode, "invalid")
                evidence = [
                    "tests/" + line.split("/tests/", 1)[-1]
                    for line in completed.stdout.splitlines()
                    if line.startswith("FAILED ")
                ]
                results.append(
                    {
                        "id": name,
                        "file": filename,
                        "outcome": outcome,
                        "returncode": completed.returncode,
                        "failing_tests": evidence,
                    }
                )
            except subprocess.TimeoutExpired:
                results.append({"id": name, "outcome": "timeout"})
    valid = [r for r in results if r["outcome"] in ("killed", "survived")]
    hashes = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((ROOT / "src/narrative_contracts").glob("*.py"))
    }
    payload = {
        "scope": "Eight hand-selected source mutants; not an exhaustive mutation score",
        "baseline": "passed",
        "source_hashes": hashes,
        "mutants": results,
        "valid": len(valid),
        "killed": sum(r["outcome"] == "killed" for r in valid),
    }
    payload["score"] = payload["killed"] / len(valid) if valid else None
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))
    if len(valid) != len(MUTANTS) or payload["killed"] != len(valid):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
