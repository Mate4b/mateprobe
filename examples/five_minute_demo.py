"""Five-minute, offline walkthrough of the narrative-contracts API.

The transition below is ordinary application code. It produces scalar state
snapshots before a reply is constructed; the contract runner only checks the
snapshots and the explicit declarations attached to the reply. In particular,
it does not decide whether arbitrary prose entails those declarations.
"""

from __future__ import annotations

from dataclasses import dataclass

from narrative_contracts import (
    Claim,
    Context,
    DeclaredClaimsConsistent,
    Document,
    MinimumTokens,
    Report,
    RequiredFact,
    StateChanged,
    Status,
    Surface,
    evaluate,
)
from narrative_contracts.engine import Contract
from narrative_contracts.model import Scalar
from narrative_contracts.mutations import (
    MutationCase,
    Relation,
    Sample,
    Target,
    Validity,
    audit,
    replace_text,
)

REPLY = "support.reply"
DOMAIN_KEYS = ("refund.decision", "refund.eligible", "refund.action")


@dataclass(frozen=True)
class Order:
    """Small trusted input projection for this deterministic example."""

    days_since_delivery: int = 10
    refund_window_days: int = 30


def trusted_transition(order: Order) -> tuple[str, dict[str, Scalar]]:
    """Return a branch and its post-state without reading generated text."""

    eligible = order.days_since_delivery <= order.refund_window_days
    branch = "refund_eligible" if eligible else "refund_ineligible"
    return branch, {
        "request.kind": "refund",
        "refund.decision": "eligible" if eligible else "ineligible",
        "refund.eligible": eligible,
        "refund.action": "issue" if eligible else "deny",
        "refund_window_days": order.refund_window_days,
    }


def branch_state(order: Order, eligible: bool) -> dict[str, Scalar]:
    """Materialize the alternative post-state for the branch table."""

    return {
        "request.kind": "refund",
        "refund.decision": "eligible" if eligible else "ineligible",
        "refund.eligible": eligible,
        "refund.action": "issue" if eligible else "deny",
        "refund_window_days": order.refund_window_days,
    }


def make_sample(
    order: Order,
    text: str,
    claims: tuple[Claim, ...],
) -> Sample:
    """Build a document from the already selected trusted state."""

    branch, selected_state = trusted_transition(order)
    current: dict[str, Scalar] = {
        "request.kind": "refund",
        "refund.decision": "pending",
        "refund.eligible": None,
        "refund.action": "pending",
        "refund_window_days": order.refund_window_days,
    }
    states: dict[str, dict[str, Scalar]] = {"current": current}
    if branch == "refund_eligible":
        states[branch] = selected_state
        states["refund_ineligible"] = branch_state(order, False)
    else:
        states["refund_eligible"] = branch_state(order, True)
        states[branch] = selected_state
    return Sample(
        Document((Surface(REPLY, text, state_ref=branch, claims=claims),)),
        Context(states),
    )


def contracts(selected_branch: str) -> tuple[Contract, ...]:
    """Contracts used in all three walkthrough cases."""

    return (
        RequiredFact("support-request", "request.kind", "refund", "current"),
        StateChanged("refund-transition", "current", selected_branch, DOMAIN_KEYS),
        DeclaredClaimsConsistent("branch-claims", (REPLY,)),
        MinimumTokens("reply-length", (REPLY,), minimum=12, minimum_unique=8),
    )


def show_diagnosis(label: str, sample: Sample, report: Report) -> None:
    """Print each finding so the accepted/rejected decision is inspectable."""

    print(f"\n{label}: accepted={report.accepted}, complete={report.complete}")
    for check in report.checks:
        print(
            f"  {check.status.value:11} {check.rule_id}/{check.code} "
            f"@ {check.scope}: {check.evidence}"
        )
    print(f"  text: {sample.document.surface(REPLY).text}")


def main() -> None:
    order = Order()
    branch, post_state = trusted_transition(order)
    print("1. state -> text -> contract -> diagnosis")
    print(f"trusted transition: {branch} -> {post_state}")

    good_text = (
        "Your refund request qualifies under the 30-day support window. "
        "We will issue the refund to the original payment method."
    )
    good_claims = (Claim("refund.eligible", True), Claim("refund.action", "issue"))
    good = make_sample(order, good_text, good_claims)
    rules = contracts(branch)
    good_report = evaluate(good.document, good.context, rules)
    show_diagnosis("accepted example", good, good_report)
    assert good_report.accepted and good_report.complete

    wrong_claims = (Claim("refund.eligible", False), Claim("refund.action", "deny"))
    wrong = make_sample(order, good_text, wrong_claims)
    wrong_report = evaluate(wrong.document, wrong.context, rules)
    show_diagnosis("wrong-branch declaration", wrong, wrong_report)
    assert not wrong_report.accepted
    assert any(
        check.status == Status.VIOLATED
        and check.rule_id == "branch-claims"
        and check.code == "CLAIM_STATE_MISMATCH"
        and check.scope == REPLY
        for check in wrong_report.checks
    )

    contradictory = make_sample(
        order,
        "Your refund request is ineligible under the policy, so the refund will be denied "
        "even though eligibility was approved.",
        good_claims,
    )
    contradictory_report = evaluate(contradictory.document, contradictory.context, rules)
    show_diagnosis("prose contradiction (accepted by design)", contradictory, contradictory_report)
    assert contradictory_report.accepted and contradictory_report.complete
    print("  diagnosis: declarations match trusted state; free prose entailment is unchecked")

    target = Target("branch-claims", "CLAIM_STATE_MISMATCH", REPLY)
    fault = MutationCase(
        "wrong-branch-claim",
        "branch-declaration",
        Relation.VIOLATION,
        good,
        wrong,
        expected=(target,),
        validity=Validity.VALID,
        provenance="Manually constructed by copying the ineligible branch declarations.",
    )
    control = MutationCase(
        "valid-paraphrase",
        "wording-preservation",
        Relation.PRESERVE,
        good,
        replace_text(
            good,
            REPLY,
            "This order meets our refund policy, so payment returns to the original method.",
        ),
        validity=Validity.VALID,
        provenance="Authored control keeps the same refund outcome.",
    )
    campaign = audit((fault, control), rules)
    campaign.assert_thresholds()
    print("\n2. mini mutation audit")
    for result in campaign.cases:
        print(f"  {result.id}: {result.outcome} ({result.reason})")
    print(f"  summary: {campaign.summary()}")
    assert campaign.summary()["detection_score"] == 1.0
    assert campaign.summary()["preservation_rate"] == 1.0


if __name__ == "__main__":
    main()
