from __future__ import annotations

from copy import deepcopy

import pytest

from narrative_contracts.mutations import Relation, Validity
from narrative_contracts.validator_audit import (
    AuditCase,
    Obligation,
    Verdict,
    audit_validator,
)

OBL = Obligation("state", "The state must remain valid")


def case(
    case_id: str,
    baseline: object,
    variant: object,
    *,
    relation: Relation = Relation.VIOLATION,
    expected: tuple[str, ...] = ("status",),
    validity: Validity = Validity.VALID,
) -> AuditCase[object]:
    return AuditCase(case_id, OBL.id, baseline, variant, relation, expected, validity, "reviewed")


def accepted(value: object) -> Verdict:
    return Verdict(True, evidence=(f"accepted:{value}",))


def test_reject_all_baseline_failure_is_excluded_from_fault_denominator():
    report = audit_validator(
        lambda value: Verdict(False, ("status",)),
        (case("reject-all", 0, 1),),
        obligations=(OBL,),
        validator_id="v1",
    )
    result = report.cases[0]
    assert result.outcome == "baseline_failed"
    assert report.summary()["eligible_faults"] == 0
    with pytest.raises(AssertionError):
        report.assert_thresholds()


def test_unrelated_rejection_is_not_detection():
    def validator(value: object) -> Verdict:
        return accepted(value) if value == "good" else Verdict(False, ("other",))

    report = audit_validator(
        validator, (case("wrong-id", "good", "bad"),), obligations=(OBL,), validator_id="v1"
    )
    assert report.cases[0].outcome == "unattributed_rejection"
    assert report.summary()["detected_faults"] == 0


def test_variant_crash_and_unknown_stay_in_fault_denominator():
    def validator(value: object) -> Verdict:
        if value == "crash":
            raise RuntimeError("boom")
        if value == "unknown":
            return Verdict(False, complete=False)
        return accepted(value)

    report = audit_validator(
        validator,
        (case("crash", "base", "crash"), case("unknown", "base", "unknown")),
        obligations=(OBL,),
        validator_id="v1",
    )
    assert [c.outcome for c in report.cases] == ["error", "undetermined"]
    assert report.summary()["eligible_faults"] == 2
    assert report.summary()["detected_faults"] == 0


def test_correct_target_and_control_are_scored():
    def validator(value: object) -> Verdict:
        return accepted(value) if value in ("ok", "still-ok") else Verdict(False, ("status",))

    control = case("control", "ok", "still-ok", relation=Relation.PRESERVE, expected=())
    report = audit_validator(
        validator, (case("fault", "ok", "bad"), control), obligations=(OBL,), validator_id="v1"
    )
    assert [c.outcome for c in report.cases] == ["detected", "preserved"]
    summary = report.summary()
    assert summary["detection_score"] == 1.0
    assert summary["preservation_rate"] == 1.0


def test_corpus_hash_is_repeatable_and_inputs_are_isolated():
    baseline = {"items": [1]}
    variant = {"items": [2]}
    seen: list[object] = []

    def mutating_validator(value: object) -> Verdict:
        seen.append(deepcopy(value))
        assert isinstance(value, dict)
        value["items"].append(99)
        return accepted(value)

    audit_case = case("isolation", baseline, variant)
    first = audit_validator(
        mutating_validator, (audit_case,), obligations=(OBL,), validator_id="v1"
    )
    second = audit_validator(
        mutating_validator, (audit_case,), obligations=(OBL,), validator_id="v1"
    )
    assert first.corpus_digest == second.corpus_digest
    assert baseline == {"items": [1]}
    assert variant == {"items": [2]}
    assert first.cases[0].baseline_digest != first.cases[0].variant_digest


def test_unreviewed_equivalent_and_noop_cases_skip_callback():
    calls = 0

    def validator(value: object) -> Verdict:
        nonlocal calls
        calls += 1
        return accepted(value)

    cases = (
        case("unreviewed", 1, 2, validity=Validity.UNREVIEWED),
        case("equivalent", 1, 2, validity=Validity.EQUIVALENT),
        case("noop", 3, 3),
    )
    report = audit_validator(validator, cases, obligations=(OBL,), validator_id="v1")
    assert calls == 0
    assert [c.outcome for c in report.cases] == ["excluded", "excluded", "excluded"]


def test_obligation_without_cases_is_visible_as_untested():
    untouched = Obligation("untouched", "No authored case exists yet")
    report = audit_validator(
        lambda value: accepted(value),
        (case("one", 1, 2),),
        obligations=(OBL, untouched),
        validator_id="v1",
    )
    row = next(row for row in report.summary()["obligations"] if row["id"] == "untouched")
    assert row["case_ids"] == []
    assert row["counts"] == {}
    assert "untested" in report.to_markdown()


def test_malformed_configurations_are_rejected():
    with pytest.raises(ValueError):
        AuditCase("bad", "state", 1, 2, Relation.VIOLATION, (), Validity.VALID, "reviewed")
    with pytest.raises(ValueError):
        audit_validator(
            lambda value: accepted(value),
            (case("same", 1, 2), case("same", 3, 4)),
            obligations=(OBL,),
            validator_id="v1",
        )
    with pytest.raises(ValueError):
        audit_validator(
            lambda value: accepted(value),
            (case("unknown", 1, 2),),
            obligations=(Obligation("other", "other"),),
            validator_id="v1",
        )
    with pytest.raises(ValueError):
        audit_validator(lambda value: accepted(value), (), obligations=(OBL,), validator_id="v1")


def test_regressed_control_does_not_earn_a_passing_audit():
    def validator(value):
        return Verdict(value == 1, () if value == 1 else ("status",))

    report = audit_validator(
        validator,
        (case("fault", 1, -1), case("control", 1, 2, relation=Relation.PRESERVE, expected=())),
        obligations=(OBL,),
        validator_id="rejects-valid-variant",
    )
    assert report.summary()["detection_score"] == 1
    assert report.summary()["preservation_rate"] == 0
    with pytest.raises(AssertionError, match="control.*regressed"):
        report.assert_thresholds()


def test_malformed_verdict_is_execution_error_not_detection():
    report = audit_validator(
        lambda n: Verdict(True) if n == 1 else False,
        (case("bad-return", 1, -1),),
        obligations=(OBL,),
        validator_id="bad-adapter",
    )
    assert report.cases[0].outcome == "error"
    assert report.summary()["detection_score"] == 0
    with pytest.raises(AssertionError, match="variant_error"):
        report.assert_thresholds(detection=0, preservation=0)


def test_rejects_accidental_string_sequences():
    with pytest.raises(TypeError):
        Verdict(False, "status")
    with pytest.raises(TypeError):
        AuditCase("fault", "state", 1, 2, Relation.VIOLATION, "status")
