"""Rebuild manuscript tables and claim-to-case links from verified raw evidence."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))
import external_conformance as external  # noqa: E402
import historical_followup as historical  # noqa: E402
import pytest_comparison as demonstration  # noqa: E402
import validator_study as controlled  # noqa: E402

CONTROL = ROOT / "benchmarks/validator-study"
HISTORY = ROOT / "benchmarks/historical-validator-results/compatibility-followup-v2"
EXTERNAL = ROOT / "benchmarks/external-conformance"
DEMO = ROOT / "benchmarks/pytest-comparison/evaluation"


def load(path):
    return json.loads(path.read_text())


def assert_equal(rebuilt, recorded):
    if load(rebuilt) != load(recorded):
        raise ValueError(f"Derived evidence differs from raw replay: {recorded.relative_to(ROOT)}")


def build(output):
    output.mkdir(parents=True, exist_ok=False)
    # Recompute classifications, not merely copy manuscript numbers or stored summaries.
    with tempfile.TemporaryDirectory(prefix="mateprobe-paper-") as temp:
        temp = Path(temp)
        with contextlib.redirect_stdout(io.StringIO()):
            controlled.run(CONTROL / "prepared", temp / "controlled", CONTROL / "evaluation")
            historical.verify()
            historical.base.replay(HISTORY / "captured", temp / "historical")
            external.run(EXTERNAL / "prepared", temp / "external", EXTERNAL / "evaluation")
            demonstration.run(temp / "demo")
        for folder, recorded, files in (
            (
                "controlled",
                CONTROL / "evaluation",
                ("summary.json", "comparisons.json", "audit-reports.json"),
            ),
            ("historical", HISTORY / "evaluation", ("summary.json", "audit-reports.json")),
            (
                "external",
                EXTERNAL / "evaluation",
                ("summary.json", "comparisons.json", "audit-report.json"),
            ),
            ("demo", DEMO, ("summary.json", "comparisons.json", "audit-reports.json")),
        ):
            for name in files:
                assert_equal(temp / folder / name, recorded / name)
        c, h, e, d = (
            load(temp / folder / "summary.json")
            for folder in ("controlled", "historical", "external", "demo")
        )
    facts = {}

    def add(key, value, path, pointer, **extra):
        facts[key] = {
            "value": value,
            "source": str(path.relative_to(ROOT)),
            "source_sha256": controlled.sha(path),
            "pointer": pointer,
            **extra,
        }

    cp = CONTROL / "evaluation/summary.json"
    for key in ("pairs", "groups", "disagreements"):
        add(f"controlled.{key}", c[key], cp, f"/{key}")
    comparisons_path = CONTROL / "evaluation/comparisons.json"
    comparisons = load(comparisons_path)
    add(
        "controlled.classifications",
        len(comparisons),
        comparisons_path,
        "",
        operation="array_length",
    )
    add("controlled.profile_count", len(c["profiles"]), cp, "/profiles", operation="object_length")
    ct = []
    for profile, p in c["profiles"].items():
        row = {"profile": profile}
        for key in (
            "boolean_detections",
            "targeted_detections",
            "eligible_faults",
            "eligible_controls",
            "preservation_rate",
            "detection_score",
            "counts",
        ):
            add(f"controlled.{profile}.{key}", p[key], cp, f"/profiles/{profile}/{key}")
            row[key] = p[key]
        ct.append(row)
        add(
            f"controlled.{profile}.cases",
            [r["id"] for r in comparisons if r["profile"] == profile],
            comparisons_path,
            "",
            operation="select_ids_by_profile",
            profile=profile,
        )
    ht = []
    hp = HISTORY / "evaluation/summary.json"
    for key in ("screened", "included", "excluded", "fixes_reproduced"):
        add(f"historical.{key}", h[key], hp, f"/{key}")
    for i, row in enumerate(h["results"]):
        ht.append(row)
        add(f"historical.{row['id']}", row, hp, f"/results/{i}")
    ep = EXTERNAL / "evaluation/summary.json"
    for key in (
        "pairs",
        "source_tests",
        "source_groups",
        "paired_groups",
        "disagreements",
        "ledger_status",
    ):
        add(f"external.{key}", e[key], ep, f"/{key}")
    for key in (
        "eligible_faults",
        "eligible_controls",
        "detected_faults",
        "preserved_controls",
        "counts",
    ):
        add(f"external.{key}", e["audit"][key], ep, f"/audit/{key}")
    for family, row in e["by_family"].items():
        add(f"external.{family}", row, ep, f"/by_family/{family}")
    dp = DEMO / "summary.json"
    for key in ("paired_classifications", "disagreements", "pytest_exit_code"):
        add(f"demo.{key}", d[key], dp, f"/{key}")
    for profile, row in d["profiles"].items():
        add(f"demo.{profile}", row, dp, f"/profiles/{profile}")
    tables = {"controlled": ct, "historical": ht, "external": e["by_family"], "demo": d["profiles"]}
    controlled.write_json(output / "tables.json", tables)
    controlled.write_json(output / "facts.json", facts)
    controlled.write_json(
        output / "manifest.json",
        {
            "schema_version": 1,
            "generator_sha256": controlled.sha(Path(__file__)),
            "revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "dirty_checkout": bool(
                subprocess.check_output(
                    ["git", "status", "--porcelain"], cwd=ROOT, text=True
                ).strip()
            ),
            "verified_by": "offline raw-verdict replay plus fresh execution of both refund validators and pytest",
            "limitation": "Replay does not re-execute historical or external packages. Mutable hashes are not attestations.",
            "files": {
                name: controlled.sha(output / name) for name in ("tables.json", "facts.json")
            },
        },
    )
    lines = [
        "# Generated manuscript evidence",
        "",
        "Rebuilt from checked captures; refund pytest comparison executed afresh.",
        "",
        "| Claim | Value | Source and JSON pointer |",
        "|---|---|---|",
    ]
    for key, fact in facts.items():
        if key.endswith(".cases") or isinstance(fact["value"], (list, dict)):
            continue
        lines.append(f"| `{key}` | {fact['value']} | `{fact['source']}#{fact['pointer']}` |")
    lines.extend(
        ["", "Full compound values and case IDs are in facts.json; table cells are in tables.json."]
    )
    (output / "claims.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"claims": len(facts), "output": str(output), "verified": True}))
    return facts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args().output)
