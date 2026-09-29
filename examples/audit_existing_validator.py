"""Offline teaching example: audit a refund validator without Context or Claim.

The business validator and receipts are illustrative, not production observations.
No API is called and no refund is executed. See lifecard_validator_audit.py for an
opt-in integration with an independently existing application validator.
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from narrative_contracts.mutations import Relation, Validity
from narrative_contracts.provenance import observe_git
from narrative_contracts.validator_audit import AuditCase, Obligation, Verdict, audit_validator

Sample = dict[str, Any]


def existing_validator(sample: Sample) -> Verdict:
    """Your existing Python validator, adapted to return stable finding IDs.

    Intentionally incomplete: checks the proposal but forgets execution evidence.
    In a real integration, validate input schemas before this business validator.
    """
    trusted, action = sample["trusted"], sample["action"]
    errors = []
    if action["customer_id"] != trusted["customer_id"]:
        errors.append("customer_mismatch")
    if action["order_id"] != trusted["order_id"]:
        errors.append("order_mismatch")
    if type(action["amount_cents"]) is not int or not (
        0 < action["amount_cents"] <= trusted["max_refund_cents"]
    ):
        errors.append("amount_out_of_bounds")
    return Verdict(accepted=not errors, violations=tuple(errors))


def corrected_validator(sample: Sample) -> Verdict:
    """Add the missing postcondition. This does not retry or authorize a refund."""
    errors = list(existing_validator(sample).violations)
    if sample["claims"]["refund_completed"]:
        receipt, action = sample["receipt"], sample["action"]
        supported = (
            receipt is not None
            and receipt["status"] == "completed"
            and receipt["request_id"] == sample["request_id"]
            and all(
                receipt[key] == action[key] for key in ("customer_id", "order_id", "amount_cents")
            )
        )
        if not supported:
            # A timeout does NOT prove failure. It fails to support a success claim.
            errors.append("completion_not_supported")
    return Verdict(accepted=not errors, violations=tuple(errors))


OBLIGATIONS = (
    Obligation("customer", "The action concerns the authenticated customer."),
    Obligation("order", "The action concerns the authorized order."),
    Obligation("amount", "Positive integer cents do not exceed the authoritative limit."),
    Obligation("completion", "A success claim needs a matching completed receipt."),
    Obligation(
        "prose",
        "The user-facing text must not contradict the evidence (scope challenge).",
        scope="challenge",
    ),
    Obligation("idempotency", "Repeated requests must not execute twice (not tested here)."),
)


def cases() -> tuple[AuditCase[Sample], ...]:
    # YOUR APP builds trusted facts and receipts, never the language model.
    baseline: Sample = {
        "request_id": "request-123",
        "trusted": {
            "customer_id": "customer-1",
            "order_id": "order-8",
            "max_refund_cents": 6000,
        },
        "action": {"customer_id": "customer-1", "order_id": "order-8", "amount_cents": 5000},
        "receipt": {
            "request_id": "request-123",
            "customer_id": "customer-1",
            "order_id": "order-8",
            "amount_cents": 5000,
            "status": "completed",
        },
        "claims": {"refund_completed": True},
        "message": "Confirmamos la devolución de 50 euros.",
    }
    result = []

    def add(
        id: str,
        obligation: str,
        variant: Sample,
        expected: str,
        reason: str,
        base: Sample = baseline,
    ) -> None:
        result.append(
            AuditCase(
                id=id,
                obligation=obligation,
                baseline=base,
                variant=variant,
                relation=Relation.VIOLATION,
                expected=(expected,),
                validity=Validity.VALID,
                provenance=f"Authored fixture: {reason}",
            )
        )

    for id, obligation, field, value, code, reason in (
        (
            "wrong-customer",
            "customer",
            "customer_id",
            "customer-2",
            "customer_mismatch",
            "Action names a different customer from the authenticated subject.",
        ),
        (
            "wrong-order",
            "order",
            "order_id",
            "order-9",
            "order_mismatch",
            "Action names an order not authorized by this trusted snapshot.",
        ),
        (
            "excessive-amount",
            "amount",
            "amount_cents",
            6001,
            "amount_out_of_bounds",
            "6001 cents exceeds the 6000-cent limit.",
        ),
    ):
        variant = deepcopy(baseline)
        variant["action"][field] = value
        add(id, obligation, variant, code, reason)

    variant = deepcopy(baseline)
    variant["receipt"] = None
    add(
        "missing-receipt",
        "completion",
        variant,
        "completion_not_supported",
        "Success is claimed without a confirmation receipt; this does not prove no call occurred.",
    )
    for id, field, value, reason in (
        ("timeout", "status", "timeout", "A timeout leaves completion unknown."),
        ("accepted-not-completed", "status", "accepted", "Acceptance is not completion."),
        ("stale-receipt", "request_id", "older-request", "Receipt belongs to another request."),
        ("wrong-receipt-customer", "customer_id", "customer-2", "Receipt is for another customer."),
    ):
        variant = deepcopy(baseline)
        variant["receipt"][field] = value
        add(id, "completion", variant, "completion_not_supported", reason)

    # A valid paraphrase is a preservation control, not semantic equivalence inferred by the tool.
    variant = deepcopy(baseline)
    variant["message"] = "La devolución de 50 euros se completó."
    result.append(
        AuditCase(
            "valid-paraphrase",
            "completion",
            baseline,
            variant,
            Relation.PRESERVE,
            validity=Validity.VALID,
            provenance="Authored control: same completed receipt and facts.",
        )
    )
    pending = deepcopy(baseline)
    pending["receipt"]["status"] = "timeout"
    pending["claims"]["refund_completed"] = False
    pending["message"] = "No podemos confirmar todavía que se completó la devolución."
    result.append(
        AuditCase(
            "honest-uncertainty",
            "completion",
            baseline,
            pending,
            Relation.PRESERVE,
            validity=Validity.VALID,
            provenance="Authored control: no success claim when completion evidence is unavailable.",
        )
    )
    contradiction = deepcopy(pending)
    contradiction["message"] = "Tu devolución ya se completó."
    add(
        "prose-only-contradiction",
        "prose",
        contradiction,
        "prose_contradiction",
        "Text asserts completed refund despite timeout and unchanged false claim.",
        base=pending,
    )
    return tuple(result)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Directory for JSON and Markdown reports")
    args = parser.parse_args()
    provenance = observe_git(Path(__file__).resolve().parents[1])
    for name, validator in (("before", existing_validator), ("after", corrected_validator)):
        report = audit_validator(
            validator,
            cases(),
            obligations=OBLIGATIONS,
            validator_id=f"refund-demo/{name}/1",
            provenance=provenance,
        )
        print(report.to_markdown())
        if args.output:
            args.output.mkdir(parents=True, exist_ok=True)
            (args.output / f"{name}.json").write_text(
                json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (args.output / f"{name}.md").write_text(report.to_markdown(), encoding="utf-8")


if __name__ == "__main__":
    main()
