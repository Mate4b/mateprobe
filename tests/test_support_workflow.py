"""Tests for the independent customer-support domain example."""

import importlib.util
import sys
from pathlib import Path

import pytest

from narrative_contracts.model import Kind, Status

MODULE_PATH = Path(__file__).parents[1] / "examples" / "support_workflow.py"
SPEC = importlib.util.spec_from_file_location("support_workflow", MODULE_PATH)
assert SPEC and SPEC.loader
support = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = support
SPEC.loader.exec_module(support)


def test_trusted_transition_is_deterministic_and_does_not_read_prose():
    eligible, eligible_state = support.trusted_refund_transition(
        support.OrderSnapshot(days_since_delivery=10, refund_window_days=30)
    )
    ineligible, ineligible_state = support.trusted_refund_transition(
        support.OrderSnapshot(days_since_delivery=31, refund_window_days=30)
    )
    assert eligible == "refund_eligible"
    assert eligible_state["refund.eligible"] is True
    assert eligible_state["refund.action"] == "issue"
    assert ineligible == "refund_ineligible"
    assert ineligible_state["refund.eligible"] is False
    assert ineligible_state["refund.action"] == "deny"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"days_since_delivery": True},
        {"refund_window_days": False},
        {"days_since_delivery": 1.5},
        {"payment_captured": 1},
        {"final_sale": "false"},
    ],
)
def test_order_snapshot_rejects_bool_as_int_and_non_boolean_flags(kwargs):
    with pytest.raises((TypeError, ValueError)):
        support.OrderSnapshot(**kwargs)


def test_ineligible_text_names_the_actual_policy_reason():
    case = support.build_support_scenario(
        support.OrderSnapshot(final_sale=True, days_since_delivery=2), "valid"
    )
    assert case.expected_branch == "refund_ineligible"
    assert "final sale" in case.document.surface("support.reply").text
    assert case.evaluate().accepted


def test_valid_and_paraphrase_cases_pass():
    for variant in ("valid", "paraphrase"):
        case = support.build_support_scenario(variant=variant)
        report = case.evaluate()
        assert report.accepted
        assert report.complete
        assert case.expected_accept


def test_wrong_branch_claim_is_rejected_even_when_other_branch_matches():
    case = support.build_support_scenario(
        support.OrderSnapshot(days_since_delivery=45), "wrong_branch_claim"
    )
    report = case.evaluate()
    assert not report.accepted
    claim_checks = [c for c in report.checks if c.rule_id == "branch-claims"]
    assert any(
        c.status == Status.VIOLATED and c.code == "CLAIM_STATE_MISMATCH" for c in claim_checks
    )
    # Both branch snapshots are present, but the claim is checked against the
    # selected refund_ineligible branch and cannot use the eligible snapshot.
    assert case.document.surface("support.reply").state_ref == "refund_ineligible"


def test_cross_branch_state_cannot_mask_trusted_transition():
    case = support.build_support_scenario(
        support.OrderSnapshot(days_since_delivery=45), "cross_branch_state"
    )
    report = case.evaluate()
    assert not report.accepted
    branch_check = next(c for c in report.checks if c.rule_id == "trusted-branch")
    assert branch_check.status == Status.VIOLATED
    # Its declarations really do match the state they point at; the separate
    # exact branch invariant is what prevents that cross-branch substitution.
    declaration_checks = [c for c in report.checks if c.rule_id == "branch-claims"]
    assert declaration_checks and all(c.status == Status.SATISFIED for c in declaration_checks)


def test_declared_claims_do_not_verify_arbitrary_prose():
    case = support.build_support_scenario(variant="arbitrary_prose")
    report = case.evaluate()
    assert report.accepted
    assert case.document.surface("support.reply").claims
    assert "harbor" in case.document.surface("support.reply").text
    assert all(
        c.kind == Kind.INVARIANT
        for c in report.checks
        if c.rule_id in {"support-request", "trusted-branch", "refund-transition", "branch-claims"}
    )


def test_missing_claims_are_undetermined_and_block_strict_policy():
    case = support.build_support_scenario(variant="no_claims")
    report = case.evaluate()
    assert not report.accepted
    assert any(c.code == "CLAIMS_ABSENT" and c.status == Status.UNDETERMINED for c in report.checks)


def test_generated_cases_are_small_stable_and_labelled():
    cases = support.generate_support_cases()
    assert [case.variant for case in cases] == [
        "valid",
        "paraphrase",
        "valid",
        "wrong_branch_claim",
        "cross_branch_state",
        "arbitrary_prose",
        "no_claims",
    ]
    assert [case.evaluate().accepted for case in cases] == [case.expected_accept for case in cases]
