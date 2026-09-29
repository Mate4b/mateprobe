import pytest

from narrative_contracts.bindings import check_fields
from narrative_contracts.model import Status


def test_bindings_are_type_sensitive_and_report_mismatch():
    report = check_fields(
        {"ready": True, "count": 1},
        {"status": True, "count": 1.0},
        {"ready": "status", "count": "count"},
    )
    assert {check.scope: check.status for check in report.checks} == {
        "binding:ready->status": Status.SATISFIED,
        "binding:count->count": Status.VIOLATED,
    }
    assert report.complete


def test_missing_output_or_state_is_undetermined():
    report = check_fields({"present": "yes"}, {}, {"present": "status", "absent": "other"})
    assert all(check.status is Status.UNDETERMINED for check in report.checks)
    assert not report.accepted


def test_empty_bindings_are_invalid_configuration():
    with pytest.raises(ValueError):
        check_fields({}, {}, {})
