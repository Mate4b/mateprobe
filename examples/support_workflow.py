"""Small, deterministic customer-support workflow for the alpha release.

The order decision is made by :func:`trusted_refund_transition`, which is
ordinary Python application logic.  Generated text is kept in ``Surface``
objects and its declarations are checked against the selected post-state.
The example intentionally includes cases where declarations pass while the
prose is unrelated: declarations are evidence supplied by the caller, not a
parser or truth oracle for arbitrary prose.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from narrative_contracts import (
    Claim,
    Context,
    DeclaredClaimsConsistent,
    Document,
    ForbiddenPattern,
    MinimumTokens,
    Policy,
    RequiredFact,
    Rule,
    StateChanged,
    Status,
    Surface,
    evaluate,
)
from narrative_contracts.engine import Contract
from narrative_contracts.model import Check, Scalar

Branch = Literal["refund_eligible", "refund_ineligible"]
Variant = Literal[
    "valid",
    "paraphrase",
    "wrong_branch_claim",
    "cross_branch_state",
    "arbitrary_prose",
    "no_claims",
]

CURRENT = "current"
REPLY_SURFACE = "support.reply"
DOMAIN_KEYS = ("refund.decision", "refund.eligible", "refund.action")


@dataclass(frozen=True)
class OrderSnapshot:
    """The small trusted input projection used by this support workflow."""

    status: str = "delivered"
    days_since_delivery: int = 10
    refund_window_days: int = 30
    payment_captured: bool = True
    final_sale: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.status, str):
            raise TypeError("status must be a string")
        if type(self.days_since_delivery) is not int or type(self.refund_window_days) is not int:
            raise TypeError("delivery and window days must be integers")
        if type(self.payment_captured) is not bool or type(self.final_sale) is not bool:
            raise TypeError("payment_captured and final_sale must be booleans")
        if self.status not in {"delivered", "cancelled", "processing"}:
            raise ValueError("status must be delivered, cancelled, or processing")
        if self.days_since_delivery < 0 or self.refund_window_days < 0:
            raise ValueError("delivery and window days must be non-negative")

    def facts(self) -> dict[str, Scalar]:
        return {
            "request.kind": "refund",
            "order.status": self.status,
            "order.days_since_delivery": self.days_since_delivery,
            "policy.refund_window_days": self.refund_window_days,
            "payment.captured": self.payment_captured,
            "order.final_sale": self.final_sale,
            "refund.decision": "pending",
            "refund.eligible": None,
            "refund.action": "pending",
        }


def trusted_refund_transition(snapshot: OrderSnapshot) -> tuple[Branch, dict[str, Scalar]]:
    """Apply the local support policy and return a named branch plus its state.

    This function is the trusted transition boundary.  It never reads the
    reply text and it does not call a service or infer facts from a model.
    """

    eligible = (
        snapshot.status == "delivered"
        and snapshot.payment_captured
        and not snapshot.final_sale
        and snapshot.days_since_delivery <= snapshot.refund_window_days
    )
    branch: Branch = "refund_eligible" if eligible else "refund_ineligible"
    return branch, _state_for_branch(snapshot, eligible)


def _state_for_branch(snapshot: OrderSnapshot, eligible: bool) -> dict[str, Scalar]:
    """Materialize one branch snapshot from trusted order facts."""

    state = snapshot.facts()
    state.update(
        {
            "refund.decision": "eligible" if eligible else "ineligible",
            "refund.eligible": eligible,
            "refund.action": "issue" if eligible else "deny",
        }
    )
    return state


@dataclass(frozen=True)
class BranchSelection(Rule):
    """Exact invariant binding the reply to the trusted transition branch."""

    expected_state_ref: str
    surface_id: str = REPLY_SURFACE

    def evaluate(self, document: Document, context: Context) -> tuple[Check, ...]:
        surface = document.surface(self.surface_id)
        scope = f"{self.surface_id}:state_ref"
        if surface.state_ref != self.expected_state_ref:
            return (
                self.result(
                    Status.VIOLATED,
                    "BRANCH_SELECTION",
                    scope,
                    f"Expected {self.expected_state_ref!r}; observed {surface.state_ref!r}",
                ),
            )
        if self.expected_state_ref not in context.states:
            return (
                self.result(
                    Status.UNDETERMINED,
                    "BRANCH_UNAVAILABLE",
                    scope,
                    f"Trusted state {self.expected_state_ref!r} is missing",
                ),
            )
        return (
            self.result(
                Status.SATISFIED,
                "BRANCH_SELECTION",
                scope,
                f"Reply is bound to trusted state {self.expected_state_ref!r}",
            ),
        )


@dataclass(frozen=True)
class SupportScenario:
    """A reproducible workflow case suitable for a small benchmark."""

    snapshot: OrderSnapshot
    variant: Variant
    expected_branch: Branch
    document: Document
    context: Context
    contracts: tuple[Contract, ...]
    expected_accept: bool

    def evaluate(self, policy: Policy | None = None):
        return evaluate(self.document, self.context, self.contracts, policy)


def _text(branch: Branch, variant: Variant, snapshot: OrderSnapshot) -> str:
    if variant == "arbitrary_prose":
        return "A blue cart crossed the harbor before lunch while the warehouse lights turned on."
    if variant == "valid":
        if branch == "refund_eligible":
            return (
                f"Your refund request qualifies under the {snapshot.refund_window_days}-day support "
                "window. We will issue the refund to the original payment method."
            )
        return (
            f"Your refund request does not meet this support policy because {_ineligible_reason(snapshot)}. "
            "We cannot issue a refund for this order."
        )
    if variant == "paraphrase":
        if branch == "refund_eligible":
            return (
                "This order meets our support policy for a refund, so the payment will go back to "
                "the method used at checkout."
            )
        return (
            "The order does not meet our support policy for a refund, so no payment reversal will "
            "be issued for it."
        )
    if variant == "wrong_branch_claim":
        return _text(branch, "valid", snapshot)
    if variant == "cross_branch_state":
        return (
            f"Your request does not meet this support policy because {_ineligible_reason(snapshot)}, "
            "so we cannot issue a refund for this order."
            if branch == "refund_ineligible"
            else "Your request qualifies under the support window, so we will issue the refund."
        )
    if variant == "no_claims":
        return _text(branch, "valid", snapshot)
    raise ValueError(f"Unsupported support variant: {variant}")


def _ineligible_reason(snapshot: OrderSnapshot) -> str:
    if snapshot.status != "delivered":
        return f"the order status is {snapshot.status}"
    if not snapshot.payment_captured:
        return "the payment was not captured"
    if snapshot.final_sale:
        return "the order is marked final sale"
    return (
        f"the order is {snapshot.days_since_delivery} days old and the support window is "
        f"{snapshot.refund_window_days} days"
    )


def _claims(branch: Branch) -> tuple[Claim, ...]:
    eligible = branch == "refund_eligible"
    return (
        Claim("refund.eligible", eligible),
        Claim("refund.action", "issue" if eligible else "deny"),
    )


def build_support_scenario(
    snapshot: OrderSnapshot | None = None, variant: Variant = "valid"
) -> SupportScenario:
    """Build one deterministic case from trusted order data and a text variant.

    ``variant`` only changes the supplied document.  The branch and snapshots
    always come from :func:`trusted_refund_transition`.  This makes it useful
    for benchmark cases without allowing generated text to choose the state.
    """

    snapshot = snapshot or OrderSnapshot()
    branch, post_state = trusted_refund_transition(snapshot)
    opposite: Branch = "refund_ineligible" if branch == "refund_eligible" else "refund_eligible"
    selected_ref = opposite if variant == "cross_branch_state" else branch
    claims_branch = opposite if variant in {"wrong_branch_claim", "cross_branch_state"} else branch
    claims = () if variant == "no_claims" else _claims(claims_branch)
    surface = Surface(
        REPLY_SURFACE,
        _text(branch, variant, snapshot),
        state_ref=selected_ref,
        claims=claims,
    )
    current = snapshot.facts()
    # Both candidate snapshots are available, as they would be in a support
    # workflow that offers two possible outcomes. BranchSelection prevents a
    # reply from selecting the opposite one after the trusted transition runs.
    states = {
        CURRENT: current,
        branch: post_state,
        opposite: _state_for_branch(snapshot, opposite == "refund_eligible"),
    }
    document = Document((surface,))
    context = Context(states)
    contracts: tuple[Contract, ...] = (
        RequiredFact("support-request", "request.kind", "refund", CURRENT),
        BranchSelection("trusted-branch", branch),
        StateChanged("refund-transition", CURRENT, branch, DOMAIN_KEYS),
        DeclaredClaimsConsistent("branch-claims", (REPLY_SURFACE,)),
        # These are intentionally labelled heuristics.  They cannot establish
        # that a sentence means what its declarations say.
        MinimumTokens("reply-length", (REPLY_SURFACE,), minimum=12, minimum_unique=8),
        ForbiddenPattern(
            "unsupported-certainty",
            (r"\bguaranteed\b", r"\balways\b"),
            (REPLY_SURFACE,),
        ),
    )
    return SupportScenario(
        snapshot,
        variant,
        branch,
        document,
        context,
        contracts,
        variant in {"valid", "paraphrase", "arbitrary_prose"},
    )


def generate_support_cases() -> tuple[SupportScenario, ...]:
    """Return a small stable corpus covering valid, mutation and boundary cases."""

    eligible = OrderSnapshot(days_since_delivery=10, refund_window_days=30)
    ineligible = OrderSnapshot(days_since_delivery=45, refund_window_days=30)
    return (
        build_support_scenario(eligible, "valid"),
        build_support_scenario(eligible, "paraphrase"),
        build_support_scenario(ineligible, "valid"),
        build_support_scenario(ineligible, "wrong_branch_claim"),
        build_support_scenario(ineligible, "cross_branch_state"),
        build_support_scenario(eligible, "arbitrary_prose"),
        build_support_scenario(eligible, "no_claims"),
    )


if __name__ == "__main__":
    for case in generate_support_cases():
        report = case.evaluate()
        print(case.variant, case.expected_branch, report.accepted)
