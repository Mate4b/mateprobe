from dataclasses import dataclass, replace

import pytest

from mateprobe import Context, Document, MinimumTokens, Rule, Status, Surface
from mateprobe.mutations import (
    MutationCase,
    Relation,
    Sample,
    Target,
    Validity,
    audit,
    replace_text,
)

RULES = (MinimumTokens("thin", ("body",), minimum=4, minimum_unique=3),)
BASE = Sample(Document((Surface("body", "A varied sentence with enough words."),)), Context({}))
TARGET = Target("thin", "LOW_LEXICAL_CONTENT", "body")


def fault(**kwargs):
    return MutationCase(
        "fault",
        "truncate",
        Relation.VIOLATION,
        BASE,
        replace_text(BASE, "body", "x"),
        (TARGET,),
        Validity.VALID,
        "Construction: one word is below lexical floor",
        **kwargs,
    )


def control():
    return MutationCase(
        "control",
        "whitespace",
        Relation.PRESERVE,
        BASE,
        replace_text(BASE, "body", "  A varied sentence with enough words.\n"),
        validity=Validity.VALID,
        provenance="Whitespace preserves word sequence",
    )


def test_paired_campaign_and_thresholds():
    report = audit((fault(), control()), RULES)
    assert report.summary()["detection_score"] == 1
    assert report.summary()["preservation_rate"] == 1
    report.assert_thresholds()
    assert report.to_dict()["cases"][0]["variant"]["accepted"] is False


def test_wrong_attribution_does_not_count_as_detection():
    case = replace(fault(), expected=(replace(TARGET, scope="somewhere_else"),))
    assert audit((case,), RULES).summary()["detection_score"] == 0


@pytest.mark.parametrize("validity", [Validity.EQUIVALENT, Validity.UNREVIEWED])
def test_unverified_labels_are_excluded(validity):
    result = audit((replace(fault(), validity=validity),), RULES)
    assert result.summary()["detection_score"] is None
    assert result.cases[0].outcome == "excluded"


def test_identical_variant_is_excluded():
    assert audit((replace(fault(), variant=BASE),), RULES).cases[0].reason == "identical_variant"


def test_baseline_must_pass_before_kill_can_count():
    case = replace(fault(), baseline=replace_text(BASE, "body", "x"))
    assert audit((case,), RULES).summary()["valid_faults"] == 0


def test_exception_is_survival_not_detection():
    @dataclass(frozen=True)
    class Broken(Rule):
        def evaluate(self, document, context):
            if document.surface("body").text == "x":
                raise RuntimeError("injected evaluator failure")
            return (self.result(Status.SATISFIED, "OK", "body", ""),)

    assert audit((fault(),), (Broken("thin"),)).summary()["detection_score"] == 0


def test_no_control_denominator_cannot_claim_perfect_preservation():
    with pytest.raises(AssertionError, match="preservation_rate=None"):
        audit((fault(),), RULES).assert_thresholds()


def test_unknown_mutation_targets_rejected():
    with pytest.raises(ValueError, match="unknown rule"):
        audit((replace(fault(), expected=(replace(TARGET, rule_id="typo"),)),), RULES)


def test_duplicate_case_ids_rejected():
    with pytest.raises(ValueError, match="Duplicate"):
        audit((fault(), fault()), RULES)


def test_mutator_does_not_edit_original_and_rejects_missing_surface():
    changed = replace_text(BASE, "body", "x")
    assert BASE.document.surface("body").text != changed.document.surface("body").text
    with pytest.raises(StopIteration):
        replace_text(BASE, "missing", "x")


def test_validity_needs_provenance():
    with pytest.raises(ValueError, match="provenance"):
        replace(fault(), provenance="")
