"""Small, offline refund audit for published narrative-contracts 0.1.0a3.

Receipts and labels are authored fixtures. No API is called and no refund occurs.
In an application, trusted receipts must come from backend instrumentation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from narrative_contracts.mutations import Relation, Validity
from narrative_contracts.validator_audit import AuditCase, Obligation, Verdict, audit_validator


def existing_validator(sample):
    # Illustrative existing check: the output declaration has the right type.
    # Input shape is otherwise assumed schema-validated before this example.
    return type(sample["refund_completed"]) is bool


def before(sample):
    # Start with the real boolean result. Never copy expected findings into it.
    return Verdict(accepted=existing_validator(sample))


def after(sample):
    if not existing_validator(sample):
        return Verdict(False, ("invalid_claim_type",))
    receipt = sample["trusted_receipt"]
    if sample["refund_completed"] and not (
        receipt is not None
        and receipt["status"] == "completed"
        and receipt["request_id"] == sample["request_id"]
    ):
        return Verdict(False, ("completion_not_supported",))
    return Verdict(True)


BASELINE = {
    "request_id": "refund-42",
    "trusted_receipt": {"request_id": "refund-42", "status": "completed"},
    "refund_completed": True,
    "text": "Your refund is complete.",
}
PENDING = {
    **BASELINE,
    "trusted_receipt": None,
    "refund_completed": False,
    "text": "We cannot confirm completion yet.",
}
OBLIGATIONS = (
    Obligation("completion", "A completion claim needs a completed receipt for this request."),
    Obligation("prose", "The prose must agree with the evidence.", scope="challenge"),
)
CASES = (
    AuditCase(
        "missing-receipt",
        "completion",
        BASELINE,
        {**BASELINE, "trusted_receipt": None},
        Relation.VIOLATION,
        expected=("completion_not_supported",),
        validity=Validity.VALID,
        provenance="Authored policy: no receipt supports the positive completion claim.",
    ),
    AuditCase(
        "wrong-request",
        "completion",
        BASELINE,
        {**BASELINE, "trusted_receipt": {"request_id": "older-request", "status": "completed"}},
        Relation.VIOLATION,
        expected=("completion_not_supported",),
        validity=Validity.VALID,
        provenance="Authored policy: another request's receipt cannot support this claim.",
    ),
    AuditCase(
        "honest-pending",
        "completion",
        BASELINE,
        PENDING,
        Relation.PRESERVE,
        validity=Validity.VALID,
        provenance="Authored control: no completion assertion when a receipt is unavailable.",
    ),
    AuditCase(
        "prose-only",
        "prose",
        PENDING,
        {**PENDING, "text": "Your refund is complete."},
        Relation.VIOLATION,
        expected=("prose_contradiction",),
        validity=Validity.VALID,
        provenance="Authored challenge: only the prose falsely asserts completion; claim stays false.",
    ),
)
EXPECTED_AFTER = {
    "missing-receipt": "detected",
    "wrong-request": "detected",
    "honest-pending": "preserved",
    "prose-only": "survived",
}


def test_refund_policy(narrative):
    # Keep the prose challenge in the score. Allow exactly this known survivor;
    # exact per-case assertions prevent a different missed fault from replacing it.
    report = narrative.audit_validator(
        after,
        CASES,
        obligations=OBLIGATIONS,
        validator_id="first-refund/after/1",
        detection=2 / 3,
    )
    assert {case.id: case.outcome for case in report.cases} == EXPECTED_AFTER


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("audit-report"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for name, validator in (("before", before), ("after", after)):
        report = audit_validator(
            validator,
            CASES,
            obligations=OBLIGATIONS,
            validator_id=f"first-refund/{name}/1",
        )
        summary = report.summary()
        print(
            f"{name}: {summary['detected_faults']}/{summary['eligible_faults']} targeted faults; "
            f"{summary['preserved_controls']}/{summary['eligible_controls']} controls preserved"
        )
        for case in report.cases:
            print(f"  {case.id}: {case.outcome}")
        (args.output / f"{name}.json").write_text(json.dumps(report.to_dict(), indent=2) + "\n")
        (args.output / f"{name}.md").write_text(report.to_markdown())
    print(
        "Prose challenge stays in the denominator. Missing receipt does not prove no call occurred."
    )
    print(f"Full reports: {args.output.resolve()}")


if __name__ == "__main__":
    main()
