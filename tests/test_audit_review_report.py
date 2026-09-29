from __future__ import annotations

from typing import Any

from narrative_contracts.model import plain
from narrative_contracts.mutations import Relation, Validity
from narrative_contracts.provenance import GitProvenance, supplied_git_provenance
from narrative_contracts.validator_audit import AuditCase, Obligation, Verdict, audit_validator
from narrative_contracts.version import LIBRARY_VERSION


def accepted(value: object) -> Verdict:
    return Verdict(True, evidence=(f"accepted:{value}",))


def reviewed_case(
    case_id: str,
    baseline: object,
    variant: object,
    obligation: str,
    *,
    relation: Relation = Relation.VIOLATION,
    expected: tuple[str, ...] = ("status",),
    validity: Validity = Validity.VALID,
) -> AuditCase[object]:
    return AuditCase(
        case_id,
        obligation,
        baseline,
        variant,
        relation,
        expected,
        validity,
        "reviewed independently",
    )


def row(report: Any, obligation_id: str) -> dict[str, Any]:
    return next(item for item in report.summary()["obligations"] if item["id"] == obligation_id)


def test_excluded_cases_are_not_evidence_of_success() -> None:
    obligation = Obligation("state", "State remains valid")
    case = reviewed_case("unreviewed", 1, 2, obligation.id, validity=Validity.UNREVIEWED)
    report = audit_validator(accepted, (case,), obligations=(obligation,), validator_id="v1")

    assert report.cases[0].outcome == "excluded"
    assert row(report, obligation.id)["assessment"] == "not_evaluated"
    assert "not_evaluated" in report.to_markdown()
    assert "No gaps observed" in report.to_markdown()


def test_obligation_with_no_cases_is_explicitly_untested() -> None:
    obligation = Obligation("untouched", "No authored case exists")
    report = audit_validator(
        accepted,
        (reviewed_case("other", 1, 2, "other"),),
        obligations=(Obligation("other", "Other"), obligation),
        validator_id="v1",
    )

    assert row(report, obligation.id)["assessment"] == "untested"
    assert row(report, obligation.id)["case_ids"] == []
    assert "untested" in report.to_markdown()


def test_controls_only_and_faults_only_are_labeled() -> None:
    control_obligation = Obligation("controls", "Controls hold")
    control = reviewed_case(
        "control", "ok", "still-ok", control_obligation.id, relation=Relation.PRESERVE, expected=()
    )
    control_report = audit_validator(
        accepted, (control,), obligations=(control_obligation,), validator_id="controls"
    )
    assert row(control_report, control_obligation.id)["assessment"] == "controls_only_no_faults"

    fault_obligation = Obligation("faults", "Faults are caught")

    def rejecting(value: object) -> Verdict:
        return accepted(value) if value == "ok" else Verdict(False, ("status",))

    fault = reviewed_case("fault", "ok", "bad", fault_obligation.id)
    fault_report = audit_validator(
        rejecting, (fault,), obligations=(fault_obligation,), validator_id="faults"
    )
    assert row(fault_report, fault_obligation.id)["assessment"] == "faults_only_no_controls"


def test_partial_excluded_evidence_is_visible() -> None:
    obligation = Obligation("state", "State remains valid")
    cases = (
        reviewed_case("detected", "ok", "bad", obligation.id),
        reviewed_case("excluded", "x", "y", obligation.id, validity=Validity.UNREVIEWED),
    )

    def rejecting(value: object) -> Verdict:
        return accepted(value) if value == "ok" else Verdict(False, ("status",))

    report = audit_validator(rejecting, cases, obligations=(obligation,), validator_id="v1")
    assert row(report, obligation.id)["assessment"] == "partial_evidence"
    assert report.summary()["counts"]["excluded"] == 1
    markdown = report.to_markdown()
    assert "partial_evidence" in markdown
    assert "excluded" in markdown


def test_known_gap_and_execution_error_have_separate_markdown_sections() -> None:
    obligation = Obligation("state", "State remains valid")

    def validator(value: object) -> Verdict:
        if value == "boom":
            raise RuntimeError("failure")
        return accepted(value)

    cases = (
        reviewed_case("gap", "ok", "survives", obligation.id),
        reviewed_case("error", "ok", "boom", obligation.id),
    )
    report = audit_validator(validator, cases, obligations=(obligation,), validator_id="v1")
    markdown = report.to_markdown()
    assert report.cases[0].outcome == "survived"
    assert report.cases[1].outcome == "error"
    assert "## Known gaps" in markdown
    assert "gap" in markdown
    assert "## Incomplete evidence and execution failures" in markdown
    assert "error" in markdown


def test_challenge_remains_in_fault_score_denominator() -> None:
    obligation = Obligation("hard", "Hard challenge", scope="challenge")

    def rejecting(value: object) -> Verdict:
        return accepted(value) if value == "ok" else Verdict(False, ("status",))

    report = audit_validator(
        rejecting,
        (reviewed_case("challenge", "ok", "bad", obligation.id),),
        obligations=(obligation,),
        validator_id="v1",
    )
    summary = report.summary()
    assert summary["eligible_faults"] == 1
    assert summary["detection_score"] == 1.0
    assert row(report, obligation.id)["scope"] == "challenge"
    assert "| hard (challenge): Hard challenge |" in report.to_markdown()


def test_default_audit_does_not_inspect_git(monkeypatch: Any) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("audit unexpectedly inspected Git")

    monkeypatch.setattr("narrative_contracts.provenance.subprocess.run", fail_if_called)
    obligation = Obligation("state", "State remains valid")
    report = audit_validator(
        accepted,
        (reviewed_case("case", 1, 2, obligation.id),),
        obligations=(obligation,),
        validator_id="v1",
    )
    assert report.provenance is None
    assert report.to_dict()["provenance"] is None


def test_supplied_and_observed_metadata_are_serialized_with_schema() -> None:
    obligation = Obligation("state", "State remains valid")
    case = reviewed_case("case", 1, 2, obligation.id)
    supplied = supplied_git_provenance("a" * 40, dirty=True)
    observed = GitProvenance("b" * 64, dirty=False, source="observed")

    supplied_report = audit_validator(
        accepted, (case,), obligations=(obligation,), validator_id="v1", provenance=supplied
    )
    observed_report = audit_validator(
        accepted, (case,), obligations=(obligation,), validator_id="v1", provenance=observed
    )
    for report, expected in ((supplied_report, supplied), (observed_report, observed)):
        data = report.to_dict()
        assert data["schema_version"] == 2
        assert data["library_version"] == LIBRARY_VERSION
        assert data["provenance"] == plain(expected)


def test_markdown_escapes_table_pipes_and_newlines() -> None:
    obligation = Obligation("obl|id\nnext", "Description | with\nline")
    case = reviewed_case("case|id\nnext", 1, 2, obligation.id, validity=Validity.UNREVIEWED)
    report = audit_validator(accepted, (case,), obligations=(obligation,), validator_id="v|1\nnext")
    markdown = report.to_markdown()

    assert "v\\|1 next" in markdown
    assert "obl\\|id next" in markdown
    assert "Description \\| with line" in markdown
    assert "case\\|id next" in markdown
