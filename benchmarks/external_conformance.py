"""Frozen external conformance pairs; preparation never executes the validator."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import subprocess
from collections import Counter
from pathlib import Path
from urllib.request import urlopen

import validator_study as reference

from narrative_contracts.model import digest
from narrative_contracts.validator_audit import Obligation, audit_validator

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "benchmarks/external-conformance"
PROTOCOL = ROOT / "paper/external-conformance-protocol.md"
REVISION = "5b0ee1613e45fcc2bddac00e07c19cd49b00d8a8"
KEYWORDS = (
    "minProperties",
    "maxProperties",
    "uniqueItems",
    "contains",
    "dependentRequired",
    "propertyNames",
)
PINNED = {
    "jsonschema": "4.17.3",
    "attrs": "26.1.0",
    "pyrsistent": "0.20.0",
    "narrative-contracts": "0.1.0a3",
}


def external_reference(value):
    if isinstance(value, dict):
        return any(
            (k in ("$ref", "$dynamicRef") and isinstance(v, str) and not v.startswith("#"))
            or external_reference(v)
            for k, v in value.items()
        )
    return isinstance(value, list) and any(external_reference(v) for v in value)


def build_pairs(sources):
    rows, ledger = [], []
    for keyword in KEYWORDS:
        for gi, group in enumerate(sources[keyword]):
            baseline_index = next(
                (i for i, t in enumerate(group["tests"]) if t["valid"] is True), None
            )
            reason = (
                "external_reference"
                if external_reference(group["schema"])
                else "no_valid_baseline"
                if baseline_index is None
                else None
            )
            for ti, test in enumerate(group["tests"]):
                if type(test["valid"]) is not bool:
                    raise ValueError("Upstream validity must be a boolean")
                row_id = f"{keyword}/{gi}/{ti}"
                entry = {
                    "id": row_id,
                    "domain": keyword,
                    "group": f"{keyword}/{gi}",
                    "description": test["description"],
                    "group_description": group["description"],
                    "valid": test["valid"],
                    "baseline_index": baseline_index,
                }
                status = reason or ("baseline" if ti == baseline_index else "paired")
                if status == "paired":
                    baseline = {
                        "schema": group["schema"],
                        "data": group["tests"][baseline_index]["data"],
                    }
                    variant = {"schema": group["schema"], "data": test["data"]}
                    if digest(baseline) == digest(variant):
                        status = "identical_variant"
                    else:
                        rows.append(
                            {
                                **entry,
                                "baseline": baseline,
                                "variant": variant,
                                "relation": "preserve" if test["valid"] else "violation",
                                "expected": [] if test["valid"] else ["schema.invalid"],
                                "provenance": f"Upstream valid label at {REVISION}: "
                                f"tests/draft2020-12/{keyword}.json group {gi} test {ti}.",
                            }
                        )
                ledger.append({**entry, "status": status})
    return rows, ledger


def prepare(destination):
    destination.mkdir(parents=True, exist_ok=False)
    source = destination / "upstream"
    source.mkdir()
    urls = {f"{k}.json": f"tests/draft2020-12/{k}.json" for k in KEYWORDS}
    urls["LICENSE"] = "LICENSE"
    for local, remote in urls.items():
        url = f"https://raw.githubusercontent.com/json-schema-org/JSON-Schema-Test-Suite/{REVISION}/{remote}"
        with urlopen(url, timeout=30) as response:
            (source / local).write_bytes(response.read())
    sources = {k: json.loads((source / f"{k}.json").read_text()) for k in KEYWORDS}
    rows, ledger = build_pairs(sources)
    reference.write_json(destination / "pairs.json", rows)
    reference.write_json(destination / "ledger.json", ledger)
    (destination / "protocol.md").write_bytes(PROTOCOL.read_bytes())
    (destination / "runner.py.txt").write_bytes(Path(__file__).read_bytes())
    reference.write_json(
        destination / "manifest.json",
        {
            "upstream_revision": REVISION,
            "stage": "prepared-before-execution",
            "files": {
                str(p.relative_to(destination)): reference.sha(p)
                for p in sorted(destination.rglob("*"))
                if p.is_file()
            },
            "reference_sha256": reference.sha(Path(reference.__file__)),
            "core_sha256": {
                str(p.relative_to(ROOT)): reference.sha(p)
                for p in sorted((ROOT / "src/narrative_contracts").glob("*.py"))
            },
        },
    )
    print(
        json.dumps(
            {
                "pairs": len(rows),
                "source_tests": len(ledger),
                "ledger": dict(Counter(x["status"] for x in ledger)),
            }
        )
    )


def verify(prepared):
    manifest = json.loads((prepared / "manifest.json").read_text())
    expected_names = {
        "pairs.json",
        "ledger.json",
        "protocol.md",
        "runner.py.txt",
        "upstream/LICENSE",
    }
    expected_names |= {f"upstream/{k}.json" for k in KEYWORDS}
    if set(manifest["files"]) != expected_names or manifest["upstream_revision"] != REVISION:
        raise ValueError("Unexpected prepared manifest")
    for name, expected in manifest["files"].items():
        if reference.sha(prepared / name) != expected:
            raise ValueError(f"Prepared content changed: {name}")
    for file, expected in [
        (Path(__file__), manifest["files"]["runner.py.txt"]),
        (PROTOCOL, manifest["files"]["protocol.md"]),
        (Path(reference.__file__), manifest["reference_sha256"]),
    ]:
        if reference.sha(file) != expected:
            raise ValueError("Prepared implementation changed")
    for name, expected in manifest["core_sha256"].items():
        if not name.startswith("src/narrative_contracts/") or ".." in Path(name).parts:
            raise ValueError("Invalid core path")
        if reference.sha(ROOT / name) != expected:
            raise ValueError("Core changed since preparation")
    rows, ledger = build_pairs(
        {k: json.loads((prepared / f"upstream/{k}.json").read_text()) for k in KEYWORDS}
    )
    if rows != json.loads((prepared / "pairs.json").read_text()):
        raise ValueError("Pairs differ from upstream labels")
    if ledger != json.loads((prepared / "ledger.json").read_text()):
        raise ValueError("Ledger differs from upstream labels")
    return rows, ledger


def capture(sample):
    try:
        # Imported only during capture, never while preparing the corpus or replaying.
        from jsonschema import Draft202012Validator

        errors = list(Draft202012Validator(sample["schema"]).iter_errors(sample["data"]))
        return {
            "error": None,
            "accepted": not errors,
            "complete": True,
            "violations": ["schema.invalid"] if errors else [],
            "package_errors": [
                {
                    "validator": e.validator,
                    "path": list(e.path),
                    "schema_path": list(e.schema_path),
                    "message": e.message,
                }
                for e in errors
            ],
        }
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def analyze(rows, ledger, observations):
    if set(observations) != {r["id"] for r in rows}:
        raise ValueError("Captured case inventory mismatch")
    lookup = {}
    for row in rows:
        if set(observations[row["id"]]) != {"baseline", "variant"}:
            raise ValueError("Captured pair incomplete")
        for side in ("baseline", "variant"):
            key = digest(row[side])
            record = observations[row["id"]][side]
            if key in lookup and lookup[key] != record:
                raise ValueError("Non-deterministic captured response")
            lookup[key] = record
    report = audit_validator(
        lambda s: reference.restore(lookup[digest(s)]),
        tuple(reference.case(r) for r in rows),
        obligations=tuple(Obligation(k, f"Upstream {k} conformance.") for k in KEYWORDS),
        validator_id="jsonschema/4.17.3/Draft202012Validator/coarse-invalid",
    )
    outcomes = {r.id: r.outcome for r in report.cases}
    comparisons = [
        {
            "id": r["id"],
            "domain": r["domain"],
            "group": r["group"],
            "relation": r["relation"],
            "audit": outcomes[r["id"]],
            "detailed_pytest": reference.detailed_comparator(
                r, observations[r["id"]]["baseline"], observations[r["id"]]["variant"]
            ),
        }
        for r in rows
    ]
    summary = {
        "schema_version": 1,
        "upstream_revision": REVISION,
        "source_tests": len(ledger),
        "source_groups": len({r["group"] for r in ledger}),
        "ledger_status": dict(sorted(Counter(r["status"] for r in ledger).items())),
        "pairs": len(rows),
        "paired_groups": len({r["group"] for r in rows}),
        "disagreements": sum(r["audit"] != r["detailed_pytest"] for r in comparisons),
        "by_family": {
            k: {
                "pairs": sum(r["domain"] == k for r in rows),
                "counts": dict(
                    sorted(Counter(r["audit"] for r in comparisons if r["domain"] == k).items())
                ),
            }
            for k in KEYWORDS
        },
        "audit": report.summary(),
    }
    return summary, comparisons, report.to_dict()


def run(prepared, output, captured=None):
    rows, ledger = verify(prepared)
    output.mkdir(parents=True, exist_ok=False)
    if captured is None:
        installed = {name: importlib.metadata.version(name) for name in PINNED}
        if installed != PINNED or platform.python_version_tuple()[:2] != ("3", "12"):
            raise ValueError(
                f"Unexpected capture runtime: {installed}, {platform.python_version()}"
            )
        reference.write_json(
            output / "environment.json",
            {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "packages": installed,
                "git_revision": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip(),
            },
        )
        observations = {
            r["id"]: {side: capture(r[side]) for side in ("baseline", "variant")} for r in rows
        }
    else:
        manifest = json.loads((captured / "manifest.json").read_text())
        if manifest["prepared_manifest_sha256"] != reference.sha(prepared / "manifest.json"):
            raise ValueError("Capture belongs to another preparation")
        if manifest["observations_sha256"] != reference.sha(captured / "observations.json"):
            raise ValueError("Captured content changed")
        observations = json.loads((captured / "observations.json").read_text())
    reference.write_json(output / "observations.json", observations)
    summary, comparisons, report = analyze(rows, ledger, observations)
    for name, value in [
        ("summary.json", summary),
        ("comparisons.json", comparisons),
        ("audit-report.json", report),
    ]:
        reference.write_json(output / name, value)
    reference.write_json(
        output / "manifest.json",
        {
            "prepared_manifest_sha256": reference.sha(prepared / "manifest.json"),
            "observations_sha256": reference.sha(output / "observations.json"),
        },
    )
    if summary["disagreements"]:
        raise AssertionError("Classification disagreements retained; investigate")
    print(json.dumps({k: v for k, v in summary.items() if k != "audit"}, indent=2))
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("prepare", "capture", "replay"))
    p.add_argument("--prepared", type=Path, default=BASE / "prepared")
    p.add_argument("--output", type=Path)
    p.add_argument("--captured", type=Path)
    p.add_argument("--network", action="store_true")
    args = p.parse_args()
    if args.action == "prepare":
        if not args.network:
            p.error("Preparing upstream sources requires --network")
        prepare(args.prepared)
    else:
        if args.output is None or (args.action == "replay" and args.captured is None):
            p.error("output is required; replay requires captured")
        run(args.prepared, args.output, args.captured if args.action == "replay" else None)


if __name__ == "__main__":
    main()
