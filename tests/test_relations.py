import pytest

from narrative_contracts.engine import evaluate
from narrative_contracts.model import Context, Document, Status, Surface
from narrative_contracts.relations import AllowedTransition, CompareFields, FieldRef

DOC = Document((Surface("out", ""),))


def test_compare_fields_supports_branch_refs_and_missing_is_unknown():
    rule = CompareFields("compare", FieldRef("before", "count"), FieldRef("after", "count"), "le")
    report = evaluate(DOC, Context({"before": {"count": 2}, "after": {"count": 3}}), (rule,))
    assert report.checks[0].status is Status.SATISFIED
    missing = evaluate(DOC, Context({"before": {"count": 2}}), (rule,))
    assert missing.checks[0].status is Status.UNDETERMINED


def test_ordering_rejects_bool_and_non_numeric_values():
    rule = CompareFields("compare", FieldRef("a", "v"), FieldRef("b", "v"), "le")
    for values in ({"a": {"v": True}, "b": {"v": 2}}, {"a": {"v": "1"}, "b": {"v": "2"}}):
        report = evaluate(DOC, Context(values), (rule,))
        assert report.checks[0].status is Status.ERROR


def test_invalid_operator_and_allowed_transition():
    with pytest.raises(ValueError):
        CompareFields("compare", FieldRef("a", "v"), FieldRef("b", "v"), "gt")
    rule = AllowedTransition(
        "transition", FieldRef("a", "status"), FieldRef("b", "status"), (("draft", "ready"),)
    )
    good = evaluate(DOC, Context({"a": {"status": "draft"}, "b": {"status": "ready"}}), (rule,))
    bad = evaluate(DOC, Context({"a": {"status": "draft"}, "b": {"status": "closed"}}), (rule,))
    assert good.checks[0].status is Status.SATISFIED
    assert bad.checks[0].status is Status.VIOLATED


def test_numeric_limit_boundary_violation_and_large_integer():
    rule = CompareFields("limit", FieldRef("action", "cents"), FieldRef("policy", "max"), "le")
    for amount, expected in ((6000, Status.SATISFIED), (6001, Status.VIOLATED)):
        report = evaluate(
            DOC, Context({"action": {"cents": amount}, "policy": {"max": 6000}}), (rule,)
        )
        assert report.checks[0].status is expected
    huge = 10**400
    report = evaluate(DOC, Context({"action": {"cents": huge}, "policy": {"max": huge}}), (rule,))
    assert report.accepted


def test_typed_equality_and_transition_do_not_coerce_bool_to_integer():
    context = Context({"a": {"v": True}, "b": {"v": 1}})
    eq = CompareFields("eq", FieldRef("a", "v"), FieldRef("b", "v"))
    transition = AllowedTransition("transition", FieldRef("a", "v"), FieldRef("b", "v"), ((1, 1),))
    assert not evaluate(DOC, context, (eq, transition)).accepted
    missing = evaluate(DOC, Context({"a": {"v": True}}), (transition,))
    assert missing.checks[0].status is Status.UNDETERMINED
