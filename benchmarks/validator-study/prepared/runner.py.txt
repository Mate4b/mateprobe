"""Prepared, offline comparison of paired validator audit methods (protocol v1)."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
from collections import Counter
from copy import deepcopy
from pathlib import Path

from narrative_contracts import __version__
from narrative_contracts.model import digest
from narrative_contracts.mutations import Relation, Validity
from narrative_contracts.validator_audit import AuditCase, Obligation, Verdict, audit_validator

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "paper" / "validator-study-protocol.md"
PROFILES = (
    "correct",
    "omit-first-obligation",
    "wrong-diagnostic-ID",
    "reject-valid-variation",
    "crash-on-fault",
    "unknown-on-fault",
    "accept-all",
    "reject-all",
)
TARGETS = {
    "refund": ("completion_status", "receipt_request"),
    "shipping": ("transition", "customer"),
    "reservation": ("quantity", "resource"),
}


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def specification(domain, sample):
    """Independent policy oracle; no calls to validator implementations."""
    if domain == "refund":
        receipt = sample["receipt"]
        return {
            "completion_status": receipt is not None and receipt["status"] == "completed",
            "receipt_request": receipt is None or receipt["request"] == sample["request"],
        }
    if domain == "shipping":
        successor = {"queued": "packed", "packed": "shipped", "shipped": "delivered"}
        return {
            "transition": successor.get(sample["before"]) == sample["after"],
            "customer": sample["customer"] == sample["owner"],
        }
    return {
        "quantity": type(sample["quantity"]) is int
        and sample["quantity"] in range(1, sample["capacity"] + 1),
        "resource": sample["resource"] == sample["authoritative_resource"],
    }


def make_corpus():
    rows = []
    for domain, targets in TARGETS.items():
        for group in range(8):
            name = f"{domain}-{group}"
            if domain == "refund":
                baseline = {
                    "request": name,
                    "receipt": {"request": name, "status": "completed"},
                    "text": "Recorded.",
                }
                faults = [
                    {**baseline, "receipt": None},
                    {**baseline, "receipt": {"request": name, "status": "pending"}},
                    {**baseline, "receipt": {"request": name, "status": "accepted"}},
                    {**baseline, "receipt": {"request": name + "-other", "status": "completed"}},
                ]
                control = {
                    **baseline,
                    "request": name + "-next",
                    "receipt": {"request": name + "-next", "status": "completed"},
                }
            elif domain == "shipping":
                baseline = {
                    "before": "queued",
                    "after": "packed",
                    "customer": name,
                    "owner": name,
                    "text": "Recorded.",
                }
                faults = [
                    {**baseline, "after": state} for state in ("delivered", "cancelled", "queued")
                ] + [{**baseline, "customer": name + "-other"}]
                control = {**baseline, "before": "packed", "after": "shipped"}
            else:
                baseline = {
                    "capacity": 10 + group,
                    "quantity": 2 + group,
                    "resource": name,
                    "authoritative_resource": name,
                    "text": "Recorded.",
                }
                faults = [{**baseline, "quantity": value} for value in (0, 11 + group, -1)] + [
                    {**baseline, "resource": name + "-other"}
                ]
                control = {**baseline, "quantity": 1}
            variants = faults + [{**baseline, "text": "Acknowledged."}, control]
            for index, variant in enumerate(variants):
                row = {
                    "id": f"{name}-{index}",
                    "domain": domain,
                    "group": name,
                    "baseline": baseline,
                    "variant": variant,
                    "relation": "violation" if index < 4 else "preserve",
                    "expected": [targets[0 if index < 3 else 1]] if index < 4 else [],
                    "provenance": "Authored from protocol v1; mechanically checked by specification.",
                }
                verify_row(row)
                rows.append(row)
    return rows


def verify_row(row):
    if not all(specification(row["domain"], row["baseline"]).values()):
        raise ValueError(f"Invalid baseline: {row['id']}")
    broken = {
        key for key, holds in specification(row["domain"], row["variant"]).items() if not holds
    }
    if broken != set(row["expected"]) or (bool(broken) != (row["relation"] == "violation")):
        raise ValueError(f"Invalid relation/target: {row['id']}")
    if row["baseline"] == row["variant"]:
        raise ValueError(f"No-op: {row['id']}")


def validate(domain, sample, profile):
    """Candidate implementations see samples and profile only, never case labels."""
    failures = []
    if domain == "refund":
        receipt = sample["receipt"]
        if receipt is None or receipt["status"] != "completed":
            failures.append("completion_status")
        if receipt is not None and receipt["request"] != sample["request"]:
            failures.append("receipt_request")
    elif domain == "shipping":
        if (sample["before"], sample["after"]) not in (
            ("queued", "packed"),
            ("packed", "shipped"),
            ("shipped", "delivered"),
        ):
            failures.append("transition")
        if sample["customer"] != sample["owner"]:
            failures.append("customer")
    else:
        if type(sample["quantity"]) is not int or not 0 < sample["quantity"] <= sample["capacity"]:
            failures.append("quantity")
        if sample["resource"] != sample["authoritative_resource"]:
            failures.append("resource")
    if profile == "accept-all":
        failures = []
    elif profile == "reject-all":
        failures = ["reject_all"]
    elif profile == "omit-first-obligation":
        failures = [item for item in failures if item != TARGETS[domain][0]]
    elif profile == "wrong-diagnostic-ID" and failures:
        failures = ["unrelated_reason"]
    elif profile == "reject-valid-variation" and sample["text"] == "Acknowledged.":
        failures.append("wording")
    elif profile == "crash-on-fault" and failures:
        raise RuntimeError("authored validator crash")
    elif profile == "unknown-on-fault" and failures:
        return Verdict(False, complete=False)
    return Verdict(not failures, tuple(failures))


def capture(domain, sample, profile):
    try:
        result = validate(domain, deepcopy(sample), profile)
        return {
            "accepted": result.accepted,
            "complete": result.complete,
            "violations": list(result.violations),
            "error": None,
        }
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def detailed_comparator(row, original, changed, *, attribute=True):
    """Ordinary assertion-based comparator, independent of audit classification code."""
    if original["error"] or not original["accepted"] or not original["complete"]:
        return "baseline_failed"
    if changed["error"]:
        return "error"
    if not changed["complete"]:
        return "undetermined"
    if row["relation"] == "preserve":
        return "preserved" if changed["accepted"] else "regressed"
    if changed["accepted"]:
        return "survived"
    if not attribute:
        return "detected"
    try:
        for finding_id in row["expected"]:
            assert finding_id in changed["violations"], finding_id
    except AssertionError:
        return "unattributed_rejection"
    return "detected"


def restore(record):
    if record["error"]:
        raise RuntimeError(record["error"])
    return Verdict(record["accepted"], tuple(record["violations"]), record["complete"])


def case(row):
    return AuditCase(
        row["id"],
        row["domain"],
        row["baseline"],
        row["variant"],
        Relation(row["relation"]),
        tuple(row["expected"]),
        Validity.VALID,
        row["provenance"],
    )


def analyze(rows, observations):
    comparisons, reports, summary = [], {}, {}
    for profile in PROFILES:
        records = observations[profile]
        for domain in TARGETS:
            selected = [row for row in rows if row["domain"] == domain]
            lookup = {}
            for row in selected:
                for side in ("baseline", "variant"):
                    key = digest(row[side])
                    record = records[row["id"]][side]
                    if key in lookup and lookup[key] != record:
                        raise ValueError(
                            "Recorded validator is not deterministic for the same input"
                        )
                    lookup[key] = record
            report = audit_validator(
                lambda sample: restore(lookup[digest(sample)]),
                tuple(case(row) for row in selected),
                obligations=(
                    Obligation(domain, f"Authored {domain} policy."),
                    Obligation(domain + "-untested", "An inventoried untested obligation."),
                ),
                validator_id=f"controlled/{domain}/{profile}/1",
            )
            reports[f"{domain}/{profile}"] = report.to_dict()
            outcomes = {item.id: item.outcome for item in report.cases}
            for row in selected:
                original, changed = (records[row["id"]][side] for side in ("baseline", "variant"))
                comparisons.append(
                    {
                        "id": row["id"],
                        "domain": domain,
                        "group": row["group"],
                        "profile": profile,
                        "relation": row["relation"],
                        "boolean": detailed_comparator(row, original, changed, attribute=False),
                        "detailed_pytest": detailed_comparator(row, original, changed),
                        "audit": outcomes[row["id"]],
                    }
                )
        selected = [r for r in comparisons if r["profile"] == profile]
        eligible_faults = [
            r for r in selected if r["relation"] == "violation" and r["audit"] != "baseline_failed"
        ]
        eligible_controls = [
            r for r in selected if r["relation"] == "preserve" and r["audit"] != "baseline_failed"
        ]
        counts = Counter(r["audit"] for r in selected)
        denominator = len(eligible_faults)
        hidden_unknowns = denominator - counts["undetermined"]
        summary[profile] = {
            "counts": dict(sorted(counts.items())),
            "eligible_faults": denominator,
            "eligible_controls": len(eligible_controls),
            "boolean_detections": sum(r["boolean"] == "detected" for r in eligible_faults),
            "targeted_detections": counts["detected"],
            "detection_score": counts["detected"] / denominator if denominator else None,
            "preservation_rate": counts["preserved"] / len(eligible_controls)
            if eligible_controls
            else None,
            "boolean_success_without_target": sum(
                r["boolean"] == "detected" and r["audit"] != "detected" for r in selected
            ),
            "detailed_disagreements": sum(r["detailed_pytest"] != r["audit"] for r in selected),
            "raw_fault_rejections_ignoring_baseline": sum(
                row["relation"] == "violation"
                and not records[row["id"]]["variant"]["error"]
                and not records[row["id"]]["variant"]["accepted"]
                and records[row["id"]]["variant"]["complete"]
                for row in rows
            ),
            "ablations": {
                "without_controls": {
                    "detection_score": counts["detected"] / denominator if denominator else None,
                    "preservation_rate": None,
                },
                "invalid_error_credit_score": (counts["detected"] + counts["error"]) / denominator
                if denominator
                else None,
                "invalid_hide_unknowns": {
                    "denominator": hidden_unknowns,
                    "score": counts["detected"] / hidden_unknowns if hidden_unknowns else None,
                },
            },
        }
    return (
        {
            "schema_version": 1,
            "library_version": __version__,
            "pairs": len(rows),
            "groups": len({row["group"] for row in rows}),
            "profiles": summary,
            "disagreements": sum(s["detailed_disagreements"] for s in summary.values()),
        },
        comparisons,
        reports,
    )


def prepare(destination):
    destination.mkdir(parents=True, exist_ok=False)
    rows = make_corpus()
    write_json(destination / "corpus.json", rows)
    shutil.copyfile(PROTOCOL, destination / "protocol.md")
    shutil.copyfile(__file__, destination / "runner.py.txt")
    write_json(
        destination / "manifest.json",
        {
            "schema_version": 1,
            "stage": "prepared-before-capture",
            "pairs": len(rows),
            "files": {
                name: sha(destination / name)
                for name in ("corpus.json", "protocol.md", "runner.py.txt")
            },
        },
    )


def load_prepared(prepared):
    manifest = json.loads((prepared / "manifest.json").read_text())
    expected_files = {"corpus.json", "protocol.md", "runner.py.txt"}
    if set(manifest["files"]) != expected_files:
        raise ValueError("Unexpected prepared manifest members")
    for name, expected in manifest["files"].items():
        if sha(prepared / name) != expected:
            raise ValueError(f"Prepared content changed: {name}")
    if (
        sha(Path(__file__)) != manifest["files"]["runner.py.txt"]
        or sha(PROTOCOL) != manifest["files"]["protocol.md"]
    ):
        raise ValueError("Runner/protocol differ from prepared snapshot")
    rows = json.loads((prepared / "corpus.json").read_text())
    if len(rows) != manifest["pairs"]:
        raise ValueError("Incorrect pair count")
    for row in rows:
        verify_row(row)
    return rows


def run(prepared, output, captured=None):
    rows = load_prepared(prepared)
    output.mkdir(parents=True, exist_ok=False)
    if captured is None:
        observations = {
            profile: {
                row["id"]: {
                    side: capture(row["domain"], row[side], profile)
                    for side in ("baseline", "variant")
                }
                for row in rows
            }
            for profile in PROFILES
        }
        write_json(
            output / "environment.json",
            {"python": platform.python_version(), "library_version": __version__},
        )
    else:
        recorded_manifest = json.loads((captured / "manifest.json").read_text())
        if recorded_manifest["prepared_manifest_sha256"] != sha(prepared / "manifest.json"):
            raise ValueError("Capture belongs to another prepared corpus")
        if sha(captured / "observations.json") != recorded_manifest["observations_sha256"]:
            raise ValueError("Captured outcomes changed")
        observations = json.loads((captured / "observations.json").read_text())
    summary, comparisons, reports = analyze(rows, observations)
    write_json(output / "observations.json", observations)
    write_json(output / "summary.json", summary)
    write_json(output / "comparisons.json", comparisons)
    write_json(output / "audit-reports.json", reports)
    write_json(
        output / "manifest.json",
        {
            "prepared_manifest_sha256": sha(prepared / "manifest.json"),
            "observations_sha256": sha(output / "observations.json"),
        },
    )
    if summary["disagreements"]:
        raise AssertionError(
            "Detailed comparator disagrees: retained outputs require investigation"
        )
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "evaluate", "replay"))
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--captured", type=Path)
    args = parser.parse_args()
    if args.action == "prepare":
        prepare(args.prepared)
    else:
        if args.output is None or (args.action == "replay" and args.captured is None):
            parser.error("output is required; replay also requires captured")
        run(args.prepared, args.output, args.captured if args.action == "replay" else None)


if __name__ == "__main__":
    main()
