"""Plain pytest equivalent for the refund demo; deliberately exposes known gaps.

Run through benchmarks/pytest_comparison.py to retain failures as study evidence.
Running this file directly with pytest returns 1 because the example validators
have known surviving faults. This is intentional, not a passing regression suite.
"""

from copy import deepcopy

import audit_existing_validator as demo
import pytest

from narrative_contracts.mutations import Relation

PAIRS = [
    (name, validator, case)
    for name, validator in (
        ("before", demo.existing_validator),
        ("after", demo.corrected_validator),
    )
    for case in demo.cases()
]


@pytest.mark.parametrize(
    "name,validator,case", PAIRS, ids=[f"{name}::{case.id}" for name, _, case in PAIRS]
)
def test_paired_obligation(name, validator, case):
    baseline = validator(deepcopy(case.baseline))
    assert baseline.complete, "baseline verdict incomplete"
    assert baseline.accepted, "baseline rejected"
    changed = validator(deepcopy(case.variant))
    assert changed.complete, "variant verdict incomplete"
    if case.relation == Relation.PRESERVE:
        assert changed.accepted, "valid control rejected"
    else:
        assert not changed.accepted, "fault survived"
        assert set(case.expected) <= set(changed.violations), "expected diagnostic missing"
