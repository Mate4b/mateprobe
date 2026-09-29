import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from mateprobe.mutations import Relation, Validity, audit

spec_path = Path(__file__).parents[1] / "benchmarks" / "expanded_mutations.py"
spec = importlib.util.spec_from_file_location("expanded_mutations", spec_path)
assert spec and spec.loader
expanded = importlib.util.module_from_spec(spec)
spec.loader.exec_module(expanded)


def test_campaign_keeps_invariant_and_heuristic_evidence_separate():
    report = audit(expanded.cases(), expanded.RULES)
    summary = expanded._summary(report, expanded.cases())

    assert summary["by_kind"]["invariant"]["valid_faults"] == 5
    assert summary["by_kind"]["invariant"]["detection_score"] == 0.8
    assert summary["by_kind"]["heuristic"]["valid_faults"] == 8
    assert summary["by_kind"]["heuristic"]["detection_score"] == 0.5
    assert summary["controls"]["valid_controls"] == 5
    assert summary["controls"]["preserved_controls"] == 4
    assert summary["controls"]["preservation_rate"] == 0.8
    assert summary["controls"]["always_reject_valid_variant_acceptance"] == 0.0


def test_expected_survivors_false_positive_and_exclusions_remain_visible():
    report = audit(expanded.cases(), expanded.RULES)
    outcomes = {result.id: result.outcome for result in report.cases}

    assert outcomes["expanded/undeclared_contradiction"] == "survived"
    assert outcomes["expanded/formula_paraphrase"] == "survived"
    assert outcomes["expanded/premise_paraphrase"] == "survived"
    assert outcomes["expanded/negated_formula_control"] == "regressed"
    assert outcomes["expanded/equivalent_unicode_normalization"] == "excluded"
    assert outcomes["expanded/state_snapshot_missing"] == "excluded"
    assert outcomes["expanded/not_applicable_semantics"] == "excluded"
    excluded = [result for result in report.cases if result.outcome == "excluded"]
    assert {result.reason for result in excluded} == {"label_equivalent", "label_unreviewed"}

    for case in expanded.cases():
        if case.validity == Validity.VALID:
            assert case.provenance
        if case.relation == Relation.VIOLATION:
            assert case.expected


def test_campaign_artifacts_are_byte_identical_across_runs(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    command = [sys.executable, str(spec_path)]
    subprocess.run([*command, "--output", str(first)], check=True, capture_output=True, text=True)
    subprocess.run([*command, "--output", str(second)], check=True, capture_output=True, text=True)

    names = ("campaign.json", "corpus.json", "summary.json", "summary.md")
    for name in names:
        assert (first / name).read_bytes() == (second / name).read_bytes()
    payload = json.loads((first / "summary.json").read_text())
    assert payload["dataset"] == "expanded-synthetic-mutation-campaign-v1"
    assert payload["seed"] == expanded.SEED
