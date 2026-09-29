"""Pydantic v2 schema boundary for a narrative-contracts reply.

The branch and authoritative state are selected by application code. Pydantic
validates the structured reply and projects only an explicit allowlist into
``Claim`` objects; generated prose is never used to select state.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from narrative_contracts import (
    Claim,
    Context,
    DeclaredClaimsConsistent,
    Document,
    Surface,
    evaluate,
)

REPLY_ID = "support.reply"
CLAIM_FIELDS = {"eligible": "refund.eligible", "action": "refund.action"}


class Reply(BaseModel):
    """Structured values allowed to become declarations on the reply."""

    model_config = ConfigDict(extra="forbid", strict=True)

    eligible: bool
    action: Literal["issue", "deny"]


def trusted_transition(days_since_delivery: int, window_days: int) -> tuple[str, dict[str, object]]:
    """Choose the branch and state from trusted application inputs."""

    eligible = days_since_delivery <= window_days
    branch = "refund_eligible" if eligible else "refund_ineligible"
    state = {
        "refund.eligible": eligible,
        "refund.action": "issue" if eligible else "deny",
    }
    return branch, state


def claims_from_reply(reply: Reply) -> tuple[Claim, ...]:
    """Project only named schema fields into the package's claim model."""

    values = reply.model_dump(include=set(CLAIM_FIELDS))
    return tuple(Claim(CLAIM_FIELDS[field], values[field]) for field in CLAIM_FIELDS)


def report_for(branch: str, states: dict[str, dict[str, object]], text: str, reply: Reply):
    document = Document(
        (
            Surface(
                REPLY_ID,
                text,
                state_ref=branch,
                claims=claims_from_reply(reply),
            ),
        )
    )
    return evaluate(
        document, Context(states), (DeclaredClaimsConsistent("reply-claims", (REPLY_ID,)),)
    )


def main() -> None:
    branch, authoritative = trusted_transition(days_since_delivery=10, window_days=30)
    states = {branch: authoritative}
    print(f"trusted branch: {branch}; authoritative state: {authoritative}")

    valid = Reply(eligible=True, action="issue")
    accepted = report_for(
        branch,
        states,
        "Your refund is approved and will be issued to the original payment method.",
        valid,
    )
    assert accepted.accepted and accepted.complete
    print("valid structured reply: accepted")

    try:
        Reply.model_validate({"eligible": 1, "action": "issue"})
    except ValidationError as error:
        assert any(item["loc"] == ("eligible",) for item in error.errors())
        print("malformed bool numeric: rejected by strict schema")
    else:  # pragma: no cover - protects the example if strictness is removed
        raise AssertionError("strict bool validation unexpectedly accepted 1")

    mismatch = Reply(eligible=True, action="deny")
    mismatch_report = report_for(
        branch,
        states,
        "Your refund is approved, but this response takes the denial path.",
        mismatch,
    )
    assert not mismatch_report.accepted
    assert any(check.code == "CLAIM_STATE_MISMATCH" for check in mismatch_report.checks)
    print("structurally valid state mismatch: rejected by declared-claim check")

    prose_contradiction = report_for(
        branch,
        states,
        "Your refund is denied, although the application state says it is approved.",
        valid,
    )
    assert prose_contradiction.accepted and prose_contradiction.complete
    print("prose-only contradiction: accepted; arbitrary prose entailment is unchecked")


if __name__ == "__main__":
    main()
