from dataclasses import dataclass

import pytest

from narrative_contracts import (
    Claim,
    Context,
    DeclaredClaimsConsistent,
    Document,
    ForbiddenPattern,
    LexicalRestatement,
    MinimumTokens,
    NoRepeatedText,
    Policy,
    RequiredFact,
    Rule,
    SettledPremise,
    StateChanged,
    Status,
    Surface,
    evaluate,
)
from narrative_contracts.model import Check, Kind


def document(text="A concrete scene with enough different words to describe the consequence."):
    return Document((Surface("body", text),))


def check(rule, doc=None, context=None, policy=None):
    return evaluate(doc or document(), context or Context({"current": {}}), (rule,), policy)


def test_state_is_copied_and_read_only():
    source = {"current": {"status": "open"}}
    ctx = Context(source)
    source["current"]["status"] = "closed"
    assert ctx.states["current"]["status"] == "open"
    with pytest.raises(TypeError):
        ctx.states["current"]["status"] = "closed"


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), [], {}, object()])
def test_facts_reject_non_json_scalars(bad):
    with pytest.raises((TypeError, ValueError)):
        Context({"current": {"x": bad}})


@pytest.mark.parametrize("actual,expected", [(True, 1), (1, 1.0), ("1", 1), (None, "None")])
def test_fact_comparison_is_type_sensitive(actual, expected):
    assert not check(
        RequiredFact("fact", "x", expected), context=Context({"current": {"x": actual}})
    ).accepted


def test_missing_fact_is_not_false_or_success():
    report = check(RequiredFact("fact", "x", False))
    assert report.checks[0].status == Status.UNDETERMINED
    assert not report.accepted and not report.complete


def test_claims_are_scoped_to_their_branch():
    doc = Document(
        (Surface("outcome", "The offer is accepted.", "reject", (Claim("offer", "accepted"),)),)
    )
    ctx = Context({"accept": {"offer": "accepted"}, "reject": {"offer": "rejected"}})
    report = check(DeclaredClaimsConsistent("claims"), doc, ctx)
    assert report.checks[0].status == Status.VIOLATED
    assert report.checks[0].scope == "outcome"


def test_unannotated_prose_is_not_certified_truthful():
    report = check(DeclaredClaimsConsistent("claims"))
    assert not report.accepted
    assert report.checks[0].code == "CLAIMS_ABSENT"


def test_correct_declarations_do_not_validate_other_prose():
    doc = Document((Surface("body", "An unrelated fabricated story.", claims=(Claim("x", 1),)),))
    report = check(DeclaredClaimsConsistent("claims"), doc, Context({"current": {"x": 1}}))
    assert report.accepted  # Explicitly document the boundary of this invariant.


@pytest.mark.parametrize("after", [{"x": 1, "turn": 2}, {"x": 1, "turn": 1}])
def test_bookkeeping_and_noop_do_not_count_as_domain_change(after):
    ctx = Context({"before": {"x": 1, "turn": 1}, "after": after})
    assert not check(StateChanged("advance", "before", "after", ("x",)), context=ctx).accepted


def test_state_change_accepts_real_difference():
    assert check(
        StateChanged("advance", "a", "b", ("x",)), context=Context({"a": {"x": 0}, "b": {"x": 1}})
    ).accepted


@pytest.mark.parametrize("text", ["a" * 70, "a" * 1000, "palabra " * 100, "123 456 789"])
def test_lexical_floor_rejects_simple_padding(text):
    assert not check(MinimumTokens("thin", ("body",)), document(text)).accepted


@pytest.mark.parametrize("length", [89, 90, 150, 1000])
def test_padding_has_no_character_cutoff_bypass(length):
    label = "Aceptar la propuesta formal"
    doc = Document((Surface("label", label), Surface("body", label + " " + "x" * length)))
    assert not check(LexicalRestatement("overlap", "label", "body"), doc).accepted


def test_real_lexical_novelty_can_pass_restatement():
    doc = Document(
        (
            Surface("label", "Aceptar la propuesta formal"),
            Surface(
                "body",
                "Aceptar la propuesta formal obliga al equipo a contratar dos especialistas nuevos.",
            ),
        )
    )
    assert check(LexicalRestatement("overlap", "label", "body"), doc).accepted


@pytest.mark.parametrize(
    "text", ["La reunión salió bien", "La reunion salio bien", "LA REUNIO\u0301N SALIO\u0301 BIEN"]
)
def test_pattern_normalizes_case_accents_and_unicode(text):
    assert not check(
        ForbiddenPattern("formula", (r"la reunion salio bien",), ("body",)), document(text)
    ).accepted


def test_formula_heuristic_has_documented_negation_false_positive():
    report = check(
        ForbiddenPattern("formula", (r"la reunion salio bien",), ("body",)),
        document("Nadie dijo que la reunión salió bien: fue un desastre."),
    )
    assert not report.accepted
    assert report.checks[0].kind == Kind.HEURISTIC


def test_premises_depend_on_context():
    rule = SettledPremise("premise", (("offer", "te ofrecen un contrato"),), ("body",))
    doc = document("Te ofrecen un contrato para firmar mañana.")
    assert check(rule, doc).accepted
    assert not check(rule, doc, Context({"current": {}}, ("offer",))).accepted
    assert not check(rule, doc, Context({"current": {}}, ("unknown",))).complete


def test_history_detects_normalized_repeat():
    assert not check(
        NoRepeatedText("repeat", ("body",)),
        document("Hola, mundo!"),
        Context({"current": {}}, history=("HOLA mundo",)),
    ).accepted


def test_policy_can_make_heuristics_advisory_without_hiding_them():
    report = check(
        MinimumTokens("thin", ("body",)), document("short"), policy=Policy(block_heuristics=False)
    )
    assert report.accepted and report.checks[0].status == Status.VIOLATED


def test_missing_surface_is_error_and_always_blocks():
    report = check(MinimumTokens("thin", ("missing",)), policy=Policy(False, False))
    assert not report.accepted and report.checks[0].status == Status.ERROR


def test_reports_are_reproducible_and_config_sensitive():
    a = check(MinimumTokens("thin", ("body",)))
    b = check(MinimumTokens("thin", ("body",)))
    c = check(MinimumTokens("thin", ("body",), minimum=11))
    assert a.to_dict() == b.to_dict()
    assert a.contracts_digest != c.contracts_digest
    assert a.input_digest == c.input_digest


@pytest.mark.parametrize("rules", [(), (RequiredFact("x", "a", 1), RequiredFact("x", "b", 2))])
def test_empty_or_duplicate_contracts_are_configuration_errors(rules):
    with pytest.raises(ValueError):
        evaluate(document(), Context({}), rules)


def test_rule_errors_and_misattribution_cannot_pass():
    @dataclass(frozen=True)
    class BadRule(Rule):
        def evaluate(self, document, context):
            return (Check("another-rule", "1", Kind.INVARIANT, Status.SATISFIED, "OK", "$", ""),)

    assert check(BadRule("bad")).checks[0].status == Status.ERROR


def test_unknown_fact_and_real_violation_have_distinct_results():
    rule = RequiredFact("fact", "x", "a")
    unknown = check(rule)
    violated = check(rule, context=Context({"current": {"x": "b"}}))
    assert unknown.checks[0].status != violated.checks[0].status


def test_duplicate_surface_ids_rejected():
    with pytest.raises(ValueError):
        Document((Surface("x", "one"), Surface("x", "two")))


def test_invalid_result_status_cannot_be_accepted():
    @dataclass(frozen=True)
    class InvalidStatus(Rule):
        def evaluate(self, document, context):
            return (Check(self.rule_id, "1", Kind.INVARIANT, "anything", "OK", "$", ""),)

    report = check(InvalidStatus("bad"))
    assert report.checks[0].status == Status.ERROR
    assert not report.accepted
