"""Check the one-file launch recipe using installed a4 packages, outside the checkout."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)

    def run(label: str, command: list[str], expected: int = 0) -> str:
        result = subprocess.run(
            [sys.executable, "-I", *command], cwd=output, capture_output=True, text=True
        )
        (output / f"{label}.log").write_text(result.stdout + result.stderr)
        if result.returncode != expected:
            raise RuntimeError(
                f"{label}: expected exit {expected}, got {result.returncode}\n"
                f"{result.stdout}{result.stderr}"
            )
        return result.stdout

    installation = json.loads(
        run(
            "installation",
            [
                "-c",
                "import json, importlib.metadata as m, mateprobe as n; "
                "print(json.dumps({'path': n.__file__, 'runtime': n.__version__, 'versions': "
                "{p: m.version(p) for p in ['mateprobe', 'pytest-mateprobe']}}))",
            ],
        )
    )
    package_path = Path(installation["path"]).resolve()
    if package_path.is_relative_to(ROOT) or "site-packages" not in package_path.parts:
        raise RuntimeError("Use installed distributions, not an editable checkout")
    assert installation["runtime"] == "0.1.0a4"
    assert set(installation["versions"].values()) == {"0.1.0a4"}
    script = output / "first_audit.py"
    shutil.copyfile(ROOT / "examples/first_audit.py", script)
    run("demo", [str(script), "--output", str(output / "reports")])
    reports = [
        json.loads((output / "reports" / f"{name}.json").read_text())
        for name in ("before", "after")
    ]
    assert reports[0]["corpus_digest"] == reports[1]["corpus_digest"]
    assert reports[0]["summary"]["counts"] == {"survived": 3, "preserved": 1}
    assert reports[1]["summary"]["counts"] == {"detected": 2, "survived": 1, "preserved": 1}
    expected_after = {
        "missing-receipt": "detected",
        "wrong-request": "detected",
        "honest-pending": "preserved",
        "prose-only": "survived",
    }
    assert {case["id"]: case["outcome"] for case in reports[1]["cases"]} == expected_after

    def check_pytest(label: str, path: Path, exit_code: int) -> dict:
        report_path = output / f"{label}.json"
        run(
            label,
            [
                "-m",
                "pytest",
                "-q",
                "-c",
                os.devnull,
                str(path),
                f"--mateprobe-report={report_path}",
            ],
            expected=exit_code,
        )
        records = json.loads(report_path.read_text())["reports"]
        assert len(records) == 1
        return records[0]

    good = check_pytest("regression-kept", script, 0)
    assert {c["id"]: c["outcome"] for c in good["cases"]} == expected_after
    source = script.read_text()
    needle = "        after,\n        CASES,"
    assert source.count(needle) == 1
    broken = output / "removed_fix.py"
    broken.write_text(source.replace(needle, "        before,\n        CASES,"))
    removed = check_pytest("regression-removed", broken, 1)
    assert removed["summary"]["counts"] == {"preserved": 1, "survived": 3}
    reject_all = output / "reject_all.py"
    reject_all.write_text(
        source.replace(
            needle,
            '        lambda sample: Verdict(False, ("completion_not_supported",)),\n        CASES,',
        )
    )
    rejected = check_pytest("reject-all", reject_all, 1)
    assert rejected["summary"]["counts"] == {"baseline_failed": 4}
    summary = {
        "status": "passed",
        "versions": installation["versions"],
        "python": sys.version.split()[0],
        "source_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
        "corpus_digest": reports[1]["corpus_digest"],
        "before": reports[0]["summary"],
        "after": reports[1]["summary"],
        "pytest_checks": {
            "fixed": "passed",
            "removed_fix": "failed as expected; JSON retained",
            "reject_all": "failed as expected; JSON retained",
        },
        "scope": "Authored demo compatibility and regression behavior, not independent adoption.",
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(
        "Launch recipe passed from installed a4; removing the fix and reject-all fail with reports."
    )


if __name__ == "__main__":
    main()
