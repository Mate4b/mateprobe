"""Prepare authored mutations of captured outputs, then evaluate the frozen corpus offline."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import re
import unicodedata
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from narrative_contracts.model import digest
from narrative_contracts.mutations import MutationCase, Relation, Sample, Target, Validity, audit

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "natural_for_mutations", ROOT / "benchmarks/natural.py"
)
assert SPEC and SPEC.loader
natural = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(natural)
PROFILE = "real-output-mutations-v1"
# Defined independently of evaluated outcomes. Semantic challenges have no detection targets.
OPERATORS = (
    ("claim_credits", "exact", ("claims", "CLAIM_STATE_MISMATCH", "outcome.0")),
    ("branch_claims", "exact", ("claims", "CLAIM_STATE_MISMATCH", "outcome.0")),
    ("empty_body", "heuristic", ("content", "LOW_LEXICAL_CONTENT", "body")),
    ("lexical_restatement", "heuristic", ("restatement.0", "LEXICAL_RESTATEMENT", "outcome.0")),
    ("literal_formula", "heuristic", ("formula", "FORBIDDEN_PATTERN", "body")),
    ("missing_claim", "schema", None),
    ("boolean_credits", "schema", None),
    ("branch_order", "schema", None),
    ("whitespace", "control", None),
    ("unicode_nfd", "control", None),
    ("prose_wrong_credits", "challenge", None),
    ("prose_wrong_status", "challenge", None),
)


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def mutate(data, scenario, name):
    variant = copy.deepcopy(data)
    first, other = variant["options"]
    if name == "claim_credits":
        first["claims"]["credits"] += 1
    elif name == "branch_claims":
        first["claims"] = copy.deepcopy(other["claims"])
    elif name == "empty_body":
        variant["body"] = ""
    elif name == "lexical_restatement":
        first["outcome"] = " ".join([first["label"]] * 12)
    elif name == "literal_formula":
        variant["body"] = (
            "Sin duda, " if scenario["language"] == "es" else "Without a doubt, "
        ) + variant["body"]
    elif name == "missing_claim":
        del first["claims"]["credits"]
    elif name == "boolean_credits":
        first["claims"]["credits"] = True
    elif name == "branch_order":
        variant["options"].reverse()
    elif name in ("whitespace", "unicode_nfd"):

        def transform(text):
            return (
                " \n" + re.sub(r"\s+", "  \n", text) + "\n "
                if name == "whitespace"
                else unicodedata.normalize("NFD", text)
            )

        variant["body"] = transform(variant["body"])
        for option in variant["options"]:
            for key in ("label", "outcome"):
                option[key] = transform(option[key])
    elif name == "prose_wrong_credits":
        wrong = scenario["options"][0]["after"]["credits"] + 100
        first["outcome"] += (
            f" Tu saldo después de esta elección es exactamente {wrong} créditos."
            if scenario["language"] == "es"
            else f" Your balance after this choice is exactly {wrong} credits."
        )
    elif name == "prose_wrong_status":
        wrong = scenario["options"][1]["after"]["status"]
        first["outcome"] += (
            f" El estado después de esta elección es exactamente {wrong}."
            if scenario["language"] == "es"
            else f" The status after this choice is exactly {wrong}."
        )
    else:
        raise ValueError(f"Unknown operator: {name}")
    return variant


def prepare(input_dir, output_dir):
    if output_dir.exists():
        raise FileExistsError("Prepared corpus must be new")
    manifest, records = natural.load_collection(input_dir)
    scenarios = {s["id"]: s for s in manifest["scenarios"]}
    cases, unavailable = [], []
    for record in records:
        scenario = scenarios[record["scenario_id"]]
        if record["collection_status"] != "returned" or not record.get("response", {}).get("done"):
            unavailable.append({"id": record["id"], "reason": "generation_unavailable"})
            continue
        raw = record["response"]["response"]
        try:
            # Parsing checks shape only; no contract verdict is used to select variants.
            natural.document(raw, scenario)
            data = natural.strict_json(raw)
        except (ValueError, KeyError, TypeError):
            unavailable.append({"id": record["id"], "reason": "baseline_invalid_structure"})
            continue
        for name, lane, target in OPERATORS:
            variant = mutate(data, scenario, name)
            cases.append(
                {
                    "id": f"{record['id']}/{name}",
                    "base_id": record["id"],
                    "model": record["model"],
                    "scenario_id": scenario["id"],
                    "group": scenario["group"],
                    "family": name,
                    "lane": lane,
                    "target": asdict(Target(*target)) if target else None,
                    "operator_version": 1,
                    "baseline_json_digest": digest(data),
                    "variant_json_digest": digest(variant),
                    "variant": variant,
                    "provenance": f"Authored operator {name}; definition in frozen protocol; no natural semantic gold label.",
                }
            )
    protocol = (ROOT / "paper/real-mutation-protocol.md").read_bytes()
    payload = {
        "profile": PROFILE,
        "source_corpus_digest": digest(records),
        "source_manifest": manifest,
        "source_records": records,
        "rule_configuration": [r.configuration() for r in natural.rules()],
        "protocol_sha256": hashlib.sha256(protocol).hexdigest(),
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "adapter_sha256": hashlib.sha256((ROOT / "benchmarks/natural.py").read_bytes()).hexdigest(),
        "operators": OPERATORS,
        "unavailable_baselines": unavailable,
        "cases": cases,
    }
    output_dir.mkdir(parents=True)
    write(output_dir / "prepared.json", payload)
    (output_dir / "SHA256SUMS").write_text(
        f"{hashlib.sha256((output_dir / 'prepared.json').read_bytes()).hexdigest()}  prepared.json\n"
    )
    (output_dir / "protocol.md").write_bytes(protocol)
    (output_dir / "generator-source.py.txt").write_bytes(Path(__file__).read_bytes())
    (output_dir / "adapter-source.py.txt").write_bytes(
        (ROOT / "benchmarks/natural.py").read_bytes()
    )
    return {"prepared_cases": len(cases), "unavailable_baselines": unavailable}


def accepted(result):
    return (
        result["status"] == "evaluated"
        and result["report"]["accepted"]
        and result["report"]["complete"]
    )


def changed_record(record, data):
    result = copy.deepcopy(record)
    result["response"]["response"] = json.dumps(data, ensure_ascii=False)
    return result


def summarize(rows):
    lanes = {}
    for lane in ("exact", "heuristic", "schema", "control", "challenge"):
        selected = [r for r in rows if r["lane"] == lane]
        counts = dict(Counter(r["outcome"] for r in selected))
        eligible = len(selected) - counts.get("excluded", 0)
        lanes[lane] = {"total": len(selected), "eligible": eligible, "counts": counts}
        if lane in ("exact", "heuristic", "schema"):
            lanes[lane]["detection_rate"] = (
                counts.get("detected", 0) / eligible if eligible else None
            )
        elif lane == "control":
            lanes[lane]["preservation_rate"] = (
                counts.get("preserved", 0) / eligible if eligible else None
            )
    return lanes


def run(prepared_dir, output_dir):
    if output_dir.exists():
        raise FileExistsError("Evaluation output must be new")
    raw = (prepared_dir / "prepared.json").read_bytes()
    expected_hash = (prepared_dir / "SHA256SUMS").read_text().split()[0]
    if hashlib.sha256(raw).hexdigest() != expected_hash:
        raise ValueError("Prepared corpus hash mismatch")
    payload = natural.strict_json(raw)
    for filename, key in (
        ("protocol.md", "protocol_sha256"),
        ("generator-source.py.txt", "generator_sha256"),
        ("adapter-source.py.txt", "adapter_sha256"),
    ):
        if hashlib.sha256((prepared_dir / filename).read_bytes()).hexdigest() != payload[key]:
            raise ValueError("Frozen source/protocol hash mismatch")
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != payload["generator_sha256"]:
        raise ValueError("Use the frozen generator version")
    if (
        hashlib.sha256((ROOT / "benchmarks/natural.py").read_bytes()).hexdigest()
        != payload["adapter_sha256"]
    ):
        raise ValueError("Use the frozen adapter version")
    if payload["profile"] != PROFILE or payload["rule_configuration"] != [
        r.configuration() for r in natural.rules()
    ]:
        raise ValueError("Frozen profile mismatch")
    if digest(payload["source_records"]) != payload["source_corpus_digest"]:
        raise ValueError("Source corpus mismatch")
    scenarios = {s["id"]: s for s in payload["source_manifest"]["scenarios"]}
    records = {r["id"]: r for r in payload["source_records"]}
    if len(records) != len(payload["source_records"]) or len(
        {c["id"] for c in payload["cases"]}
    ) != len(payload["cases"]):
        raise ValueError("Duplicate source/case id")
    baseline = {
        rid: natural.evaluate_record(r, scenarios[r["scenario_id"]]) for rid, r in records.items()
    }
    rows, contract_cases = [], []
    for case in payload["cases"]:
        record, scenario = records[case["base_id"]], scenarios[case["scenario_id"]]
        if (
            digest(case["variant"]) != case["variant_json_digest"]
            or digest(natural.strict_json(record["response"]["response"]))
            != case["baseline_json_digest"]
        ):
            raise ValueError("Case input/output digest mismatch")
        base = baseline[case["base_id"]]
        row = {k: v for k, v in case.items() if k != "variant"}
        reason = ""
        if not accepted(base):
            reason = "baseline_not_accepted_and_complete"
        elif natural.strict_json(record["response"]["response"]) == case["variant"]:
            reason = "identical_variant"
        if reason:
            rows.append({**row, "outcome": "excluded", "reason": reason, "result": None})
            continue
        variant_record = changed_record(record, case["variant"])
        result = natural.evaluate_record(variant_record, scenario)
        lane = case["lane"]
        if lane in ("exact", "heuristic", "control"):
            ctx = natural.context(scenario)
            mutation = MutationCase(
                id=case["id"],
                family=case["family"],
                group=case["group"],
                relation=Relation.PRESERVE if lane == "control" else Relation.VIOLATION,
                baseline=Sample(natural.document(record["response"]["response"], scenario), ctx),
                variant=Sample(
                    natural.document(variant_record["response"]["response"], scenario), ctx
                ),
                expected=(Target(**case["target"]),) if case["target"] else (),
                validity=Validity.VALID,
                provenance=case["provenance"],
            )
            contract_cases.append(mutation)
            outcome = "pending_audit"
        elif lane == "schema":
            outcome = "detected" if result["status"] == "invalid_structure" else "survived"
        else:
            outcome = "accepted" if accepted(result) else "rejected_without_semantic_attribution"
        rows.append({**row, "outcome": outcome, "reason": reason, "result": result})
    campaign = audit(tuple(contract_cases), natural.rules())
    audited = {r.id: r for r in campaign.cases}
    for row in rows:
        if row["id"] in audited:
            row["outcome"] = audited[row["id"]].outcome
            row["reason"] = audited[row["id"]].reason
    summary = {
        "profile": PROFILE,
        "prepared_sha256": expected_hash,
        "source_corpus_digest": payload["source_corpus_digest"],
        "baseline_records": len(records),
        "baselines_accepted": sum(accepted(b) for b in baseline.values()),
        "scenario_groups": len({r["group"] for r in records.values()}),
        "cases": len(rows),
        "unavailable_baselines": payload["unavailable_baselines"],
        "by_lane": summarize(rows),
        "by_model": {
            m: summarize([r for r in rows if r["model"] == m])
            for m in sorted({r["model"] for r in rows})
        },
        "by_family": {
            f: dict(Counter(r["outcome"] for r in rows if r["family"] == f))
            for f, _, _ in OPERATORS
        },
        "violation_findings_by_family": {
            family: dict(
                Counter(
                    f"{c['rule_id']}/{c['code']}/{c['scope']}"
                    for row in rows
                    if row["family"] == family and row["result"]
                    for c in row["result"].get("report", {}).get("checks", [])
                    if c["status"] == "violated"
                )
            )
            for family, _, _ in OPERATORS
        },
        "interpretation": "Authored faults on accepted real-output baselines; no natural semantic accuracy, independent labels, or aggregate challenge detection score.",
    }
    output_dir.mkdir(parents=True)
    write(output_dir / "summary.json", summary)
    write(output_dir / "cases.json", rows)
    write(output_dir / "baselines.json", baseline)
    # Avoid a combined exact/heuristic score: the lane-specific figures are the headline.
    write(
        output_dir / "contract-audit.json",
        {"corpus_digest": campaign.corpus_digest, "cases": campaign.to_dict()["cases"]},
    )
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--input", type=Path, required=True)
    prep.add_argument("--output", type=Path, required=True)
    run_parser = commands.add_parser("evaluate")
    run_parser.add_argument("--prepared", type=Path, required=True)
    run_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = (
        prepare(args.input, args.output)
        if args.command == "prepare"
        else run(args.prepared, args.output)
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
